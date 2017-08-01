import os

import tensorflow as tf
from datetime import datetime

from lib import data_utils
from lib.seq2seq_model_utils import create_model, get_predicted_sentence

import jieba

def predict(args, debug=False):
    def _get_test_dataset():
        with open(args.test_dataset_path) as test_fh:
            test_sentences = [s.strip() for s in test_fh.readlines()]
        return test_sentences

    def sentence_split(sentence):
        seg_list = jieba.cut(sentence, cut_all=False)
        sentence = ' '.join((' '.join(seg_list)).split())
        return sentence

    results_filename = '_'.join(['results', str(args.num_layers), str(args.size), str(args.vocab_size)])
    results_path = os.path.join(args.results_dir, results_filename+'.txt')

    # gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=args.gpu_usage)
    # with tf.Session(config=tf.ConfigProto(gpu_options=gpu_options)) as sess:
    
    if args.gpu_usage == 0:
        #config = tf.ConfigProto(device_count = {'GPU': 0})
        os.environ['CUDA_VISIBLE_DEVICES'] = ''

    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=args.gpu_usage)
    config=tf.ConfigProto(gpu_options=gpu_options)


    with tf.Session(config=config) as sess, open(results_path, 'w') as results_fh:
        # Create model and load parameters.
        args.batch_size = 1
        model = create_model(sess, args)

        # Load vocabularies.
        vocab_path = os.path.join(args.data_dir, "vocab%d.in" % args.vocab_size)
        vocab, rev_vocab = data_utils.initialize_vocabulary(vocab_path)

        test_dataset = _get_test_dataset()

        for sentence in test_dataset:
            # Get token-ids for the input sentence.
            sentence = sentence_split(sentence)
            predicted_sentence = get_predicted_sentence(args, sentence, vocab, rev_vocab, model, sess, debug=debug)
            if isinstance(predicted_sentence, list):
                print("input: %s  (%s)" % (sentence, datetime.now()))
                results_fh.write("input: %s  (%s)\n" % (sentence, datetime.now()))
                for sent in predicted_sentence:
                    print("chatbot: %s  (%s)" % (sent['dec_inp'], sent['prob']))
                    results_fh.write("chatbot: %s  (%f)\n" % (sent['dec_inp'], sent['prob']))
            else:
                print(sentence, ' -> ', predicted_sentence)
                results_fh.write("%s -> %s\n" % (sentence, predicted_sentence))

    results_fh.close()
    print("results written in %s" % results_path)
