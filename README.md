# TrafficSignRecognizer
A neural network for recognizing traffic signs in images.
The network is used in an Android app for recording images through the windscreen of a car and remembering the last sign.
Even though that it is function, do not use it while driving since it is mostly a distraction from the road.

## App
The Android app can be downloaded [here](https://github.com/Aggrathon/TrafficSignRecognizer/releases).  
When evaluated on the training material it reached a precision of 99.6%.
Since it was trained on roughly 30 000 images this accuracy doesn't seem to be due to overfitting.
In practise it has difficulties with tunnels and anything not recorded from a road but is otherwise pretty accurate.
Since it is only trained on Finnish signs, your experience may vary.


## Neural Network
The `data` folder contains some scipt for easily sort through source material and prepare it for learning.  
Use `train.py` to train the network and `export.py` to prepare the trained model for use in the app.
In the `model.py` is the layout of the network defined and it looks like this:

| Convolution 1 | Convolution 2 | Convolution 3 | Fully Connected 1 | Fully Connected 2 | Prediction |
| ------------- | ------------- | ------------- | ----------------- | ----------------- | ---------- |
| Size: 32      | Size: 48      | Size: 64      | Size: 256         | Size: 64          | Size: 1    |
| Conv2d ReLU   | Conv2d ReLU   | Conv2d ReLU   | ReLU              | ReLU              | Sigmoid    |
| Max Pooling   | Max Pooling   | Max Pooling   | Dropout           | Dropout           |            |
| Normalization | Normalization | Normalization |                   |                   |            |


## Dependencies
- Python 3
- Tensorflow
- Pygame (for source material sorting)

