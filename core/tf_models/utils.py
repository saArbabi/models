import tensorflow as tf
from tensorflow_probability import distributions as tfd
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")
# %%
# %%
def get_CovMatrix(rhos, sigmas_long, sigmas_lat):
    covar = tf.math.multiply(tf.math.multiply(sigmas_lat,sigmas_long),rhos)

    col1 = tf.stack([tf.math.square(sigmas_long), covar], axis=2, name='stack')
    col2 = tf.stack([covar, tf.math.square(sigmas_lat)], axis=2, name='stack')
    # sigmas_long**2 is covariance of sigmas_long with itself
    cov = tf.stack([col1, col2], axis=2, name='cov')
    return cov[0]

def get_pdf(parameter_vector, model_type):

    if model_type == '///':
        alpha, mus, sigmas = slice_pvector(parameter_vector, model_type) # Unpack parameter vectors
        mvn = tfd.MixtureSameFamily(
            mixture_distribution=tfd.Categorical(probs=alpha),
            components_distribution=tfd.Normal(
                loc=mus,
                scale=sigmas))

    if model_type == 'merge_policy':
        alphas, mus_long, sigmas_long, mus_lat, sigmas_lat, rhos = slice_pvector(
                                                            parameter_vector, model_type)

        cov = get_CovMatrix(rhos, sigmas_long, sigmas_lat)
        mvn = tfd.MixtureSameFamily(
            mixture_distribution=tfd.Categorical(
                probs=alphas),
            components_distribution=tfd.MultivariateNormalTriL(
                loc=tf.stack([mus_long, mus_lat], axis=2, name='mu'),
                scale_tril=tf.linalg.cholesky(cov), name='MultivariateNormalTriL'))
    return mvn

def slice_pvector(parameter_vector, model_type):
    """ Returns an unpacked list of paramter vectors.
    """
    if model_type == '///':
        n_params = 3 # number of parameters being learned
    if model_type == 'merge_policy':
        n_params = 6

    if tf.is_tensor(parameter_vector):
        return tf.split(parameter_vector, n_params, axis=1)
    else:
        return tf.split(parameter_vector, n_params, axis=0)

def covDet(parameter_vector, max_min, model_type):
    alphas, mus_long, sigmas_long, mus_lat, sigmas_lat, rhos = slice_pvector(
                                                        parameter_vector, model_type)

    covar = tf.math.multiply(tf.math.multiply(sigmas_lat,sigmas_long),rhos)
    col1 = tf.stack([tf.math.square(sigmas_long), covar], axis=2, name='stack')
    col2 = tf.stack([covar, tf.math.square(sigmas_lat)], axis=2, name='stack')
    cov = tf.stack([col1, col2], axis=2, name='cov')

    if max_min == 'max':
        return tf.math.reduce_max(tf.linalg.det(cov[0]))
    else:
        return tf.math.reduce_min(tf.linalg.det(cov[0]))

def nll_loss(y, parameter_vector, model_type):
    """ Computes the mean negative log-likelihood loss of y given the mixture parameters.
    """
    mvn = get_pdf(parameter_vector, model_type)
    log_likelihood = mvn.log_prob(y) # Evaluate log-probability of y

    return -tf.reduce_mean(log_likelihood, axis=-1)

def get_predictionMean(parameter_vector, model_type):
    mvn = get_pdf(tf.convert_to_tensor(parameter_vector), model_type)
    return mvn.mean()

def get_pdf_samples(samples_n, parameter_vector, model_type):
    mvn = get_pdf(tf.convert_to_tensor(parameter_vector), model_type)
    return mvn.sample(samples_n)
