import sys
import inspect
from RAI.AISystem import AISystem, Model
from RAI.redis import RaiRedis
from RAI.dataset import MetaDatabase, Feature, Dataset, IteratorData
import torch
import torchvision
import torchvision.transforms as transforms
import torch.nn as nn
import torch.optim as optim
import os
import random
import numpy as np
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


def main():
    os.environ["CUDA_VISIBLE_DEVICES"] = "cpu"
    torch.manual_seed(0)
    random.seed(0)
    np.random.seed(10)
    PATH = '../cifar_net.pth'

    # Get Data
    batch_size = 256
    transform = transforms.Compose([transforms.ToTensor()])
    train_set = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
    train_loader = torch.utils.data.DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=2)
    test_set = torchvision.datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
    test_loader = torch.utils.data.DataLoader(test_set, batch_size=batch_size, shuffle=False, num_workers=2)
    classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

    # Define Model
    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.features_conv = nn.Sequential(
                nn.Conv2d(3, 6, 5),
                nn.ReLU(),
                nn.MaxPool2d(2, 2),
                nn.Conv2d(6, 16, 5),
                nn.ReLU(),
            )
            self.f1 = nn.Sequential(
                nn.MaxPool2d(2, 2),
            )
            self.flatten = True
            self.classifier = nn.Sequential(
                nn.Linear(16 * 5 * 5, 120),
                nn.ReLU(),
                nn.Linear(120, 84),
                nn.ReLU(),
                nn.Linear(84, 10)
            )

        def forward(self, x):
            x = self.features_conv(x)
            x = self.f1(x)
            x = torch.flatten(x, 1)
            x = self.classifier(x)
            return x

    # Create network
    net = Net()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)

    def train():
        print("Starting training")
        for epoch in range(5):  # loop over the dataset multiple times
            running_loss = 0.0
            for i, data in enumerate(train_loader, 0):
                inputs, labels = data
                optimizer.zero_grad()
                outputs = net(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                running_loss += loss.item()
                if i % 2000 == 1999:  # print every 2000 mini-batches
                    print(f'[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}')
                    running_loss = 0.0
        torch.save(net.state_dict(), PATH)

    # Define predict function to use for RAI
    def predict_proba(input_image):
        return torch.softmax(net(input_image), 1)

    def predict(input_image):
        _, predicted = torch.max(net(input_image), 1)
        return predicted.tolist()

    # Load the model if it exists, otherwise train one
    if os.path.isfile(PATH):
        print("Loading model")
        net.load_state_dict(torch.load(PATH))
    else:
        train()
    net.eval()

    # Define the content of the dataset
    image = Feature(name='Input Image', dtype='Image', description='The 32x32 input image')
    meta = MetaDatabase([image])

    # Define the model
    outputs = Feature(name='Image class', dtype='numeric', description='The type of image',
                      categorical=True, values={i: v for i, v in enumerate(classes)})
    model = Model(agent=net, output_features=outputs, name="conv_net", predict_fun=predict, predict_prob_fun=predict_proba,
                  description="ConvNet", model_class="ConvNet", loss_function=criterion, optimizer=optimizer)
    configuration = {"time_complexity": "polynomial"}

    # Pass data splits to RAI
    dataset = Dataset({"train": IteratorData(train_loader), "test": IteratorData(test_loader)})

    # Create the RAI AISystem
    ai = AISystem(name="cifar_classification", task='classification', meta_database=meta, dataset=dataset, model=model)
    ai.initialize(user_config=configuration)

    # Generate predictions
    preds = []
    for i, vals in enumerate(test_loader, 0):
        image, label = vals
        _, predicted = torch.max(net(image), 1)
        preds += predicted

    # Compute Metrics based on the predictions
    ai.compute({"test": {"predict": preds}}, tag='Resnet')

    # View the dashboard
    r = RaiRedis(ai)
    r.connect()
    r.reset_redis()
    r.add_measurement()
    r.export_metadata()
    r.export_visualizations("test", "test")


if __name__ == '__main__':
    main()
