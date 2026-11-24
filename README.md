# GE 2340 Phase 2

## Description

The repository contains the doc and code.

## Tools

- [Overleaf](https://www.overleaf.com/) to render the Tex file. (VS code's LaTeX extension always report error and warnings)

## Methods

### KNN

shape: torch.Size([31716, 5000])
Data Size: 5000

K=5 | Test Accuracy: 0.9745
|              | precision | recall | f1-score | support |
| ------------ | --------- | ------ | -------- | ------- |
| ham          | 0.98      | 0.97   | 0.97     | 992     |
| spam         | 0.97      | 0.98   | 0.97     | 1008    |
| accuracy     |           |        | 0.97     | 2000    |
| macro avg    | 0.97      | 0.97   | 0.97     | 2000    |
| weighted avg | 0.97      | 0.97   | 0.97     | 2000    |

Accuracy with different Ks

| K    | Test Accuracy |
| :--- | :-----------: |
| 5    |    0.9669     |
| 6    |    0.9835     |
| 7    |    0.9752     |
| 8    |    0.9835     |
| 9    |    0.9835     |
| 10   |    0.9835     |
| 11   |    0.9669     |
| 12   |    0.9835     |
| 13   |    0.9752     |
| 14   |    0.9752     |
| 15   |    0.9669     |
| 16   |    0.9752     |
| 17   |    0.9752     |
| 18   |    0.9752     |
| 19   |    0.9752     |
| 20   |    0.9752     |
| 40   |    0.9587     |