from openai import OpenAI

client = OpenAI(
    base_url="https://api.deepseek.com/",
    api_key="sk-ca9d2a314fda4f8983f61e292a858d17"
)

completion = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
                "role": "system",
                "content": ""
        },
        {
                "role": "user",
                "content": """

from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import matplotlib.pyplot as plt
import torch
import CNN
import numpy as np
import os


os.makedirs('./data/EMNIST', exist_ok=True)

# 标准化数据 
data_tf = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))  
])

batch_size = 64

# 加载训练集
train_dataset = datasets.EMNIST(
    root='./data/EMNIST', 
    split='letters',
    train=True,
    transform=data_tf,
    download=True
)

test_dataset = datasets.EMNIST(
    root="./data/EMNIST",
    split='letters',
    train=False,
    transform=data_tf
)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)


CNNmodel = CNN.CNN(out=26)

# 使用Adam优化器
learning_rate = 0.001
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(CNNmodel.parameters(), lr=learning_rate)

# 训练参数
num_epochs = 50
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CNNmodel.to(device)

print(f"使用设备: {device}")
print(f"训练样本数: {len(train_dataset)}")
print(f"测试样本数: {len(test_dataset)}")
print(f"模型结构:\n{CNNmodel}")

def train():
    CNNmodel.train()
    for epoch in range(num_epochs):
        total_loss = 0
        correct = 0
        total = 0
        
        for images, labels in train_loader:
            # 将数据移动到GPU
            images, labels = images.to(device), labels.to(device)
            
            # 注意：EMNIST labels是1-26，转换为0-25
            labels = labels - 1
            
            optimizer.zero_grad()
            outputs = CNNmodel(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
        
        accuracy = 100 * correct / total
        avg_loss = total_loss / len(train_loader)
        
        print(f'Epoch [{epoch+1}/{num_epochs}], '
              f'Loss: {avg_loss:.4f}, '
              f'Accuracy: {accuracy:.2f}%')
    
    # 保存模型
    torch.save(CNNmodel.state_dict(), 'emnist_cnn_model.pth')
    print("模型已保存为 'emnist_cnn_model.pth'")

def test():
    CNNmodel.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for images, labels in test_loader:

            images, labels = images.to(device), labels.to(device)
            
            # 标签转换 (1-26 -> 0-25)
            labels = labels - 1
            
            outputs = CNNmodel(images)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    
    accuracy = 100 * correct / total
    avg_loss = total_loss / len(test_loader)
    
    print(f'\n测试结果:')
    print(f'测试损失: {avg_loss:.4f}')
    print(f'测试准确率: {accuracy:.2f}%')

def show_predict():
    CNNmodel.eval()
    loader = DataLoader(dataset=test_dataset, batch_size=9, shuffle=True)
    

    images, labels = next(iter(loader))
    

    images, labels = images.to(device), labels.to(device)
    
    # 标签转换 (1-26 -> 0-25)
    labels = labels - 1
    
    with torch.no_grad():
        outputs = CNNmodel(images)
        _, predicted = torch.max(outputs, 1)
    

    images = images.cpu()
    predicted = predicted.cpu()
    labels = labels.cpu()
    
    plt.figure(figsize=(10, 10))
    for i in range(9):
        plt.subplot(3, 3, i+1)
        

        img = images[i].squeeze().numpy() * 0.5 + 0.5
        plt.imshow(img, cmap='gray')
        

        pred_char = chr(predicted[i].item() + 65)  
        true_char = chr(labels[i].item() + 65)
        
        title = f"预测: {pred_char}, 真实: {true_char}"
        if pred_char == true_char:
            plt.title(title, color='green', fontproperties='SimSun')
        else:
            plt.title(title, color='red', fontproperties='SimSun')
        
        plt.axis('off')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    train()
    test()
    show_predict()

import torch.nn as nn

class CNN(nn.Module):
    def __init__(self, out=26):  
        super(CNN, self).__init__()
        self.out = out
        
        
        self.layer1 = nn.Sequential(
            nn.Conv2d(1, 8, kernel_size=3, padding=1),  
            nn.BatchNorm2d(8),
            nn.ReLU(inplace=True)
        )
        
        self.layer2 = nn.Sequential(
            nn.Conv2d(8, 16, kernel_size=3, padding=1),  
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)  
        )
        
        self.layer3 = nn.Sequential(
            nn.Conv2d(16, 32, kernel_size=3, padding=1), 
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True)
        )
        
        self.layer4 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),  
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)  
        )
        

        self.fc = nn.Sequential(
            nn.Linear(64*7*7, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, self.out)
        )
    
    def forward(self, x):

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = x.view(x.size(0), -1) 
        x = self.fc(x)
        return x
根据以上代码写出readme.md文件，给我原始的markdown代码，使用中文描述
                """
        }
    ]
)

print(completion.choices[0].message.content)