import os

import tqdm
from PIL import Image

from vietocr.tool.translate import build_model, translate, translate_beam_search, process_input, predict
from vietocr.tool.utils import download_weights

import torch

class Predictor():
    def __init__(self, config):

        device = config['device']
        
        model, vocab = build_model(config)

        if config['weights'].startswith('http'):
            weights = download_weights(config['weights'])
        else:
            weights = config['weights']

        try:
            model.load_state_dict(torch.load(weights, map_location=torch.device(device))['state_dict'])
        except:
            model.load_state_dict(torch.load(weights, map_location=torch.device(device)))

        self.config = config
        self.model = model
        self.vocab = vocab


        
    def predict(self, img, return_prob=False):
        img = process_input(img, self.config['dataset']['image_height'], 
                self.config['dataset']['image_min_width'], self.config['dataset']['image_max_width'], is_padding=self.config['dataset']['is_padding'])
        img = img.to(self.config['device'])

        if self.config['predictor']['beamsearch']:
            sent = translate_beam_search(img, self.model)
            s = sent
            prob = None
        else:
            s, prob = translate(img, self.model)
            s = s[0].tolist()
            prob = prob[0]

        s = self.vocab.decode(s)
        
        if return_prob:
            return s, prob
        else:
            return s



    def gen_annotations(self, anno_path, anno_out, data_root):
        with open(anno_path, 'r')  as f:
            annotations = [anno.strip().split('||||') for anno in f.readlines()]

        pred_annotations = []
        for annotation in tqdm.tqdm(annotations):
            try:

                img_path = annotation[0]
                img_fullpath = os.path.join(data_root, img_path)
                img = Image.open(img_fullpath)
                pred, prob = self.predict(img, return_prob=True)

            except Exception as err:
                print("ERROR: ", err)
                pred_annotations.append([img_path, '$$$$$', 0])
            else:
                pred_annotations.append([img_path, pred, prob])

        with open(anno_out, 'w', encoding='utf-8') as f:
            for anno in pred_annotations:
                f.write('||||'.join([anno[0], anno[1], str(float(anno[2]))]) + '\n')

        print("DONE")









