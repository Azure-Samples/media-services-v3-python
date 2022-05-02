#import * as factory from transform_factory
import transform_factory as factory

myList = {"channels":"2", "sampling_rate":"48000","bitrate":"128000"}
print(factory.createAACaudio(myList))