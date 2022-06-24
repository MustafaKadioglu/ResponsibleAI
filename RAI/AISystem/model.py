__all__ = ['Model', 'task_types']
from RAI.metrics.metric_group import all_task_types
task_types = ["binary_classification", "multiclass_classification", "regression"]


class Model:
    def __init__(self, task=None, predict_fun=None, predict_prob_fun=None, generate_text_fun=None, name=None, display_name=None, agent=None, loss_function=None, optimizer=None, model_class=None, description=None) -> None:
        assert task in all_task_types, ("task_type must be one of ", all_task_types)
        assert name is not None, "Please provide a model name"
        self.task = task
        self.output_types = []
        self.predict_fun = predict_fun
        if predict_fun is not None:
            self.output_types.append("predict")
        self.predict_prob_fun = predict_prob_fun
        if predict_prob_fun is not None:
            self.output_types.append("predict_proba")
        self.generate_text_fun = generate_text_fun
        if generate_text_fun is not None:
            self.output_types.append("generate_text")
        self.name = name
        self.display_name = name
        if display_name is not None:
            self.display_name = display_name
        self.agent = agent
        self.input_type = None
        self.loss_function = loss_function
        self.optimizer = optimizer
        self.model_class = model_class
        self.description = description
