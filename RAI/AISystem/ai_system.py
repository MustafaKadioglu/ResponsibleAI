import numpy as np
import pandas as pd
import sklearn as sk
import datetime
from RAI.metrics.registry import registry
from .task import *
from RAI.dataset import *
import os
import csv
import json



class AISystem:
    def __init__(self, meta_database, dataset, task, user_config) -> None:
        self.meta_database = meta_database
        self.task = task
        self.dataset = dataset
        self.metric_groups = {}
        self.timestamp = ""
        self.sample_count = 0
        self.user_config = user_config

    def _is_compatible(self, reqs):
        return reqs["type_restriction"] is None or reqs["type_restriction"] == self.task.type

    def initialize(self, metric_groups=None, metric_group_re=None, max_complexity="linear"):
        for metric_group_name in registry:
            temp = registry[metric_group_name](self)
            if self._is_compatible(temp.compatibility):
                self.metric_groups[metric_group_name] = temp
                print("metric group : {} was created".format(metric_group_name))

# May be more convenient to just accept metric name (or add functionality to detect group names and return a dictionary)
    def get_metric(self, metric_group_name, metric_name): 
        print("request for metric group : {}, metric_name : {}".format(metric_group_name, metric_name))
        return self.metric_groups[metric_group_name].metrics[metric_name].value

    def reset_metrics(self):
        for metric_group_name in self.metric_groups:
           self.metric_groups[metric_group_name].reset()
        self.sample_count = 0
        self.time_stamp = None  # Replace by registering a time metric in metric_groups? 

    def get_data(self, data_type):
        if data_type == "train":
            return self.dataset.train_data
        if data_type == "val":
            return self.dataset.val_data
        if data_type == "test":
            return self.dataset.test_data
        raise Exception("unknown data type : {}".format(data_type))

    def get_model_info(self):
        result = {"id": self.task.model.name, "model": self.task.model.model_class, "adaptive": self.task.model.adaptive}
        return result

    def get_metric_info(self):
        result = {}
        lists = {}
        for group in self.metric_groups:
            for metric in self.metric_groups[group].metrics:
                metric_obj = self.metric_groups[group].metrics[metric]
                result[metric] = {"name": metric_obj.name, "has_range": metric_obj.has_range, "range": metric_obj.range, "explanation": metric_obj.explanation}
                if self.metric_groups[group].category not in lists:
                    lists[self.metric_groups[group].category] = []
                lists[self.metric_groups[group].category].append(metric_obj.name)
        return {"metrics": result, "categories": lists}

    def compute_metrics(self, preds=None, reset_metrics=False, data_type="train"):
        if reset_metrics:
            self.reset_metrics()
        data_dict = {"data": self.get_data(data_type)}
        if preds is not None:
            data_dict["predictions"] = preds
        for metric_group_name in self.metric_groups:
            self.metric_groups[metric_group_name].compute(data_dict)
        self.timestamp = self._get_time()
        self.sample_count += len(data_dict)

    def update_metrics(self, data):
        for i in range(len(data)):
            for metric_group_name in self.metric_groups:
                self.metric_groups[metric_group_name].update(data[i])
        self.timestamp = self._get_time()
        self.sample_count += 1

    def get_metric_values(self):
        result = {}
        for metric_group_name in self.metric_groups:
            result[metric_group_name] = self.metric_groups[metric_group_name].export_metrics_values()
        return result

    def _get_time(self):
        now = datetime.datetime.now()
        return str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "-" + str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)

    def export_data(self, dir=None):
        if not os.path.exists(os.getcwd() + '\output'):
            os.mkdir(os.getcwd() + "\output")
        data_exists = os.path.exists(os.getcwd() + "\output\metric_values.csv")
        metric_values = self.get_metric_values()
        model_info = self.get_model_info()
        metric_info = self.get_metric_info()

        self._dict_to_csv(os.getcwd() + "\output\metric_values.csv", metric_values, not data_exists)
        with open(os.getcwd() + "\output\metric_info.json", 'w') as f:
            json.dump(metric_info["metrics"], f)
        with open(os.getcwd() + "\output\metric_list.json", 'w') as f:
            json.dump(metric_info["categories"], f)
        with open(os.getcwd() + "\output\model_info.json", 'w') as f:
            json.dump(model_info, f)

    def _dict_to_csv(self, file, dict, write_headers=True):
        newDict = {}
        newDict['date'] = self.timestamp
        for category in dict:
            for metric in dict[category]:
                newDict[metric] = dict[category][metric]
        df = pd.DataFrame([newDict])
        df.to_csv(file, header=write_headers, mode='a', index=False)







