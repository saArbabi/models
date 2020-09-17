
import os
import json
from datetime import datetime
from models.core.preprocessing.data_prep import DataPrep
import pickle

# %%
class DataObj():
    dirName = './datasets/preprocessed/'

    def __init__(self, config):
        self.config = config['data_config']
        # self.setAtt(self.config['data_id'])

    def preprocessData(self):
        """If data file does not already exist, this func creates it.
        """
        time = datetime.now().strftime("%Y%m%d-%H%M%S")

        with open(self.dirName+'config_files/'+time+'.json', 'w') as f:
            json.dump(self.config, f, indent=4, separators=(',', ': '))
        prepper = DataPrep(config,  self.dirName+time)
        prepper.data_prep('training_episodes')
        prepper.data_prep('validation_episodes')

        return time

    def loadPickledObj(self, dataFolderName):
        obj_names = ['x_train', 'y_train', 'x_val', 'y_val']
        data_objs = []

        for item in obj_names:
            with open(self.dirName+dataFolderName+'/'+item, 'rb') as f:
                data_objs.append(pickle.load(f))
        return data_objs

    def load_dataConfig(self, config_name):
            with open(self.dirName+'config_files/'+config_name, 'r') as f:
                return json.load(f)

    def loadData(self):
        config_names = os.listdir(self.dirName+'config_files')
        if not config_names:
            dataFolderName = self.preprocessData()
            return self.loadPickledObj(dataFolderName)

        else:
            for config_name in config_names:
                config = self.load_dataConfig(config_name)
                if config == self.config:
                    #load data
                    return self.loadPickledObj(config_name[:-5])

            dataFolderName = self.preprocessData()
            return self.loadPickledObj(dataFolderName)
