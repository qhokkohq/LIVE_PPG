import torch.nn as nn
import torch 

class CNN_MLP_BP(nn.Module):

    def __init__(self, num_features, output_size=2):
        super().__init__()

        # CNN branch
        self.cnn = nn.Sequential(
            nn.Conv1d(1, 16, kernel_size=7, padding=3),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.MaxPool1d(2),

            nn.Conv1d(16, 32, kernel_size=7, padding=3),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2),

            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
        )

        self.avg_pool = nn.AdaptiveAvgPool1d(1)

        # MLP branch
        self.mlp = nn.Sequential(
            nn.Linear(num_features, 64),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(64, 32),
            nn.ReLU(),
        )

        # CNN = 64
        # MLP = 32
        # Combined = 96
        self.fc = nn.Sequential(
            nn.Linear(96, 64),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(64, output_size)
        )

    def forward(self, ppg, features):

        # CNN
        x = self.cnn(ppg)
        x = self.avg_pool(x).squeeze(-1)   # (batch, 64)

        # MLP
        x_mlp = self.mlp(features)         # (batch, 32)

        # Combine
        x = torch.cat([x, x_mlp], dim=1)   # (batch, 96)

        # Prediction
        return self.fc(x)