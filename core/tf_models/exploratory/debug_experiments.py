from models.core.tf_models.cae_model import  Encoder, Decoder, CAE
from models.core.train_eval.utils import loadConfig
# from models.core.train_eval.model_evaluation import modelEvaluate
import tensorflow as tf
from models.core.tf_models import utils
from tensorflow_probability import distributions as tfd
from models.core.preprocessing.data_obj import DataObj

import numpy as np
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from importlib import reload
import time

# %%
"""
Use this script for debugging the following:
- models.core.tf_models.utils

Particularly ensure:
[] Distribution shapes are reasonable.
    See print('Distribution description: ',str(mvn))
    see print('covariance shape: ', cov.shape)
    see print('mu shape: ', mu.shape)
[] Shape of log_likelihood is reasonable
    See print('log_likelihood shape: ', log_likelihood.shape)

See:
https://www.tensorflow.org/probability/examples/Understanding_TensorFlow_Distributions_Shapes
"""
# %%

config = {
 "model_config": {
     "learning_rate": 1e-3,
     "enc_units": 20,
     "dec_units": 20,
     "layers_n": 2,
     "epochs_n": 50,
     "batch_n": 1124,
     "components_n": 5
},
"data_config": {"step_size": 1,
                "obsSequence_n": 20,
                "pred_horizon": 20,
                "m_s":["vel", "pc", "act_long_p", "act_lat_p"],
                "y_s":["vel", "dv", "dx", "act_long_p"],
                # "Note": "baseline - no time stamps"
                # "Note": "Here I am adding the time stamp"
                "Note": "cae setup"
},
"exp_id": "NA",
"model_type": "merge_policy",
"Note": "NA"
}
# %%
reload(utils)
from models.core.tf_models import utils

from models.core.tf_models import cae_model
reload(cae_model)
from models.core.tf_models.cae_model import  Encoder, Decoder, CAE

# config = loadConfig('series000exp001')
config['exp_id'] = 'debug_experiment_2'
train_loss = []
valid_loss = []


encoder_model = Encoder(config)
decoder_model = Decoder(config)
model = CAE(encoder_model, decoder_model, config)

optimizer = tf.optimizers.Adam(model.learning_rate)
data_objs =  DataObj(config).loadData()
train_ds = model.batch_data(data_objs[0:4])
test_ds = model.batch_data(data_objs[4:])

write_graph = 'False'
batch_i = 0
t0 = time.time()
for epoch in range(10):
    for states, targets_m, targets_y, conditions in train_ds:
        if write_graph == 'True':
            print(tf.shape(states))
            graph_write = tf.summary.create_file_writer(model.exp_dir+'/logs/')
            tf.summary.trace_on(graph=True, profiler=False)
            model.train_step(states, targets_m, targets_y, conditions, optimizer)
            with graph_write.as_default():
                tf.summary.trace_export(name='graph', step=0)
            write_graph = 'False'
        else:
            model.train_step(states, targets_m, targets_y, conditions, optimizer)

    for states, targets_m, targets_y, conditions in test_ds:
        model.test_step(states, targets_m, targets_y, conditions)
    train_loss.append(round(model.train_loss.result().numpy().item(), 2))
    valid_loss.append(round(model.test_loss.result().numpy().item(), 2))
# modelEvaluate(model, validation_data, config)
print('experiment duration ', time.time() - t0)


plt.plot(valid_loss)
plt.plot(train_loss)

# %%
conditions.shape
state_obs = tf.reshape(states[0], [1, 20, 10])
cond = tf.reshape(conditions[0], [1, 20, 3])
state_obs.shape
enc_state = encoder_model(state_obs)
param_vec = decoder_model([cond, enc_state])
utils.get_pdf_samples(samples_n=1, param_vec=param_vec, model_type='merge_policy')
targets[0]
# %%
"""
Recursive prediction
"""
y_feature_n = 3
t0 = time.time()
def decode_sequence(state_obs, condition, step_n):
    # Encode the input as state vectors.
    encoder_states_value = encoder_model(state_obs)

    # Sampling loop for a batch of sequences
    # (to simplify, here we assume a batch of size 1).
    sequences = []
    for n in range(1):
        states_value = encoder_states_value
        decoded_seq = []
        # Generate empty target sequence of length 1.
        # Populate the first character of target sequence with the start character.
        cond_shape = [1, 1, 3]
        conditioning  = tf.reshape(condition[0, 0, :], cond_shape)
        for i in range(20):

            param_vec = decoder_model([conditioning , states_value])
            # print(output_.stddev())
            output_ = utils.get_pdf_samples(samples_n=1, param_vec=param_vec, model_type='merge_policy')
            output_ = tf.reshape(output_, [2])
            decoded_seq.append(output_)
            # Update the target sequence (of length 1).

            if i != 19:
                cond_val  = condition[0, i+1, -1]
                conditioning  = tf.concat([output_, [cond_val]], 0)
                conditioning  = tf.reshape(conditioning, cond_shape)

            # Update states
            states_value = decoder_model.state


        sequences.append(np.array(decoded_seq))
    sequences = np.array(sequences)

    return sequences

step_n = 20
sequences = decode_sequence(state_obs, cond, step_n)
# plt.plot(state_obs.flatten())
# plt.plot(range(9, 19), decoded_seq.flatten())
compute_time = time.time() - t0
compute_time
#
plt.plot(targets[0][:, 1], color='red')
for traj in sequences:
    plt.plot(traj[:, 1], color='grey')

# plt.plot(targets[0][:, 0], color='red')
# for traj in sequences:
#     plt.plot(traj[:, 0], color='grey')
# %%