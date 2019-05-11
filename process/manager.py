from typing import Dict, List
import json
from model import ROOT_DIR
import operator
from process import composed, core
from datetime import datetime
from dateutil import relativedelta
from gmail import api


class RuleManager:

    all_fields = ["from_address", "to_address", "subject", "message_body", "received_on"]
    string_fields = ["from_address", "to_address", "subject", "message_body"]
    date_field = ["received_on"]
    date_unit_list = ["days", "months"]
    rule_dict = {}

    def __init__(self):
        self.rule_predicate = "all"
        self.date_unit = "days"
        self.query_dict = {}
        self.predicate_dict = {}
        self.all_emails = composed.extract_email_queryset()
        self.filtered_emails = []

    @staticmethod
    def load_rule_json(json_filename: str) -> Dict:
        with open(ROOT_DIR + "/config/" + json_filename, 'r') as json_file:
            RuleManager.rule_dict = json.load(json_file)
        json_file.close()
        return RuleManager.rule_dict

    @staticmethod
    def rule_predicate_converter(predicate):
        return {
            "all": operator.and_,
            "any": operator.or_
        }[predicate]

    @staticmethod
    def predicate_converter(predicate):
        return {
            "contains": operator.contains,
            "does_not_contain": operator.not_(operator.contains),
            "equals": operator.eq,
            "does_not_equal": operator.is_not,
            "less_than": operator.lt,
            "greater_than": operator.gt
        }[predicate]

    def process_operation(self, operand1, operation, operand2):
        if operation == "does_not_contain":
            return not self.predicate_converter("contains")(operand1, operand2)
        return self.predicate_converter(operation)(operand1, operand2)

    def apply_filters(self):
        current_datetime = datetime.now()
        for email in self.all_emails:
            flag_all = False
            time_delta = current_datetime - email["received_on"]
            for field, predicate in self.predicate_dict.items():
                if field in self.date_field and self.date_unit == "days":
                    operand1 = time_delta.days
                elif field in self.date_field and self.date_unit == "months":
                    operand1 = relativedelta.relativedelta(current_datetime, email["received_on"]).months
                else:
                    operand1 = email.get(field)
                if self.process_operation(operand1=operand1,
                                          operation=predicate,
                                          operand2=self.query_dict.get(field)):
                    if self.rule_predicate == "any":
                        self.filtered_emails.append(email)
                        break
                    elif self.rule_predicate == "all":
                        flag_all = True
                else:
                    if self.rule_predicate == "all":
                        flag_all = False
                        break
                    elif self.rule_predicate == "any":
                        continue
            if flag_all:
                    self.filtered_emails.append(email)


class ProcessManager:

    actions = ["mark_as", "archive", "add_label"]
    mark_as_list = ["READ", "UNREAD"]

    def __init__(self):
        self.filtered_emails = []

    def mark_read_unread(self, label) -> bool:
        message_label_obj = {
            'removeLabelIds': [],
            'addLabelIds': []
        }
        for email in self.filtered_emails:
            label_list: List = email['label'].split(',')
            if label == "READ":
                if "UNREAD" in label_list:
                    label_list.remove("UNREAD")
                    message_label_obj["removeLabelIds"].append("UNREAD")
                    email['is_read'] = True

            if label == "UNREAD":
                if "UNREAD" not in label_list:
                    label_list.append(label)
                    message_label_obj["addLabelIds"].append("UNREAD")
                    email['is_read'] = False
            email['label'] = ",".join(label_list)
            core.update_email_label(message_id=email["message_id"], label=label)
            core.update_email_status(message_id=email["message_id"], label=label)
            api.modify_message(service=api.get_gmail_service(),
                               msg_id=email["message_id"], user_id="me",
                               msg_labels=message_label_obj)
        return True

    def archive_mail(self) -> bool:
        message_label_obj = {
            'removeLabelIds': [],
            'addLabelIds': []
        }
        for email in self.filtered_emails:
            label_list: List = email['label'].split(',')
            if "INBOX" in label_list:
                label_list.remove("INBOX")
                message_label_obj["removeLabelIds"].append("INBOX")
            label = ",".join(label_list)
            email['label'] = label
            email['is_archived'] = True
            core.update_email_label(message_id=email["message_id"], label=label)
            core.change_archive_status(message_id=email["message_id"], status=True)
            api.modify_message(service=api.get_gmail_service(),
                               msg_id=email["message_id"], user_id="me",
                               msg_labels=message_label_obj)
        return True

    def add_custom_label(self, custom_label: str):
        user_labels = api.ListLabels(service=api.get_gmail_service(), user_id='me')
        all_labels = [label['name'] for label in user_labels]
        if custom_label.upper() in all_labels:
            label_dict = user_labels[all_labels.index(custom_label.upper())]
            message_label_obj = {
                'removeLabelIds': [],
                'addLabelIds': [label_dict["id"]]
            }
            for email in self.filtered_emails:
                label_list: List = email['label'].split(',')
                if custom_label.upper() not in label_list:
                    label_list.append(custom_label.upper())
                label = ','.join(label_list)
                core.update_email_label(message_id=email["message_id"], label=label)

                api.modify_message(service=api.get_gmail_service(),
                                   msg_id=email["message_id"], user_id="me",
                                   msg_labels=message_label_obj)
                email['label'] = label
            return True
        else:
            label = self.create_custom_label(label_name=custom_label.upper())
            message_label_obj = {
                'removeLabelIds': [],
                'addLabelIds': [label["id"]]
            }
            for email in self.filtered_emails:
                label_list: List = email['label'].split(',')
                if custom_label.upper() not in label_list:
                    label_list.append(custom_label.upper())
                label = ','.join(label_list)
                core.update_email_label(message_id=email["message_id"], label=label)

                api.modify_message(service=api.get_gmail_service(),
                                   msg_id=email["message_id"], user_id="me",
                                   msg_labels=message_label_obj)
                email['label'] = label
            return True

    @staticmethod
    def create_custom_label(label_name: str):
        label_object = api.MakeLabel(label_name=label_name)
        label = api.CreateLabel(service=api.get_gmail_service(), user_id='me', label_object=label_object)
        return label

    def perform_action(self, action):
        return {
            "mark_as": self.mark_read_unread,
            "archive": self.archive_mail,
            "add_label": self.add_custom_label
        }[action]