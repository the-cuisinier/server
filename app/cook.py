import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import numpy as np
import os
import pickle
from torchvision import transforms
from PIL import Image
import time
import sys

import requests
from io import BytesIO
import random
from collections import Counter


sys.path.insert(0, '/home/dewanshrawat15/Desktop/temp/server/app')
from modules.model import get_model
from modules.output_utils import prepare_output
import sys; sys.argv=['']; del sys
from modules.args import get_parser


class InverseCook:

	def convertNameToId(self, name):
		dataId = "-".join([i.lower() for i in name.split(" ")])
		return dataId
	
	def home(self, img_file):
		recipe = {}
		data_dir = "/home/dewanshrawat15/Desktop/temp/server/app/modules/"
		ingrs_vocab = pickle.load(open(os.path.join(data_dir, 'ingr_vocab.pkl'), 'rb'))
		vocab = pickle.load(open(os.path.join(data_dir, 'instr_vocab.pkl'), 'rb'))

		ingr_vocab_size = len(ingrs_vocab)
		instrs_vocab_size = len(vocab)
		output_dim = instrs_vocab_size
		use_gpu = False
		device = torch.device('cuda' if torch.cuda.is_available() and use_gpu else 'cpu')
		map_loc = None if torch.cuda.is_available() and use_gpu else 'cpu'

		t = time.time()

		args = get_parser()
		args.maxseqlen = 15
		args.ingrs_only=False
		model = get_model(args, ingr_vocab_size, instrs_vocab_size)

		model_path = os.path.join(data_dir, 'modelbest.ckpt')
		model.load_state_dict(torch.load(model_path, map_location=map_loc))
		model.to(device)
		model.eval()
		model.ingrs_only = False
		model.recipe_only = False
		print('Loaded Model')
		print("Elapsed time:", time.time() - t)
		transf_list_batch = []
		transf_list_batch.append(transforms.ToTensor())
		transf_list_batch.append(transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)))
		to_input_transf = transforms.Compose(transf_list_batch)

		greedy = [True, False, False, False]
		beam = [-1, -1, -1, -1]
		temperature = 1.0
		numgens = len(greedy)
		use_urls = True
		show_anyways = False

		# image_path = os.path.join(image_folder, )
		image = Image.open(img_file).convert('RGB')
		
		transf_list = []
		transf_list.append(transforms.Resize(256))
		transf_list.append(transforms.CenterCrop(224))
		transform = transforms.Compose(transf_list)
		
		try:
			image_transf = transform(image)
			image_tensor = to_input_transf(image_transf).unsqueeze(0).to(device)
			
			num_valid = 1
			for i in range(numgens):
				with torch.no_grad():
					try:
						outputs = model.sample(image_tensor, greedy=greedy[i], temperature=temperature, beam=beam[i], true_ingrs=None)
					except:
					  print("")

				print("Model has run")
				ingr_ids = outputs['ingr_ids']
				recipe_ids = outputs['recipe_ids']

				ingr_ids = np.asarray([[x.item() for x in ingr_ids[0]]])
				recipe_ids = np.asarray([[x.item() for x in recipe_ids[0]]])

				outs, valid = prepare_output(recipe_ids[0], ingr_ids[0], ingrs_vocab, vocab)
				if valid['is_valid'] or show_anyways:
					title = outs['title']
					print(title)
					ingredients = outs['ingrs']
					instructions = outs['recipe']
					recipeId = self.convertNameToId(title)
					recipe[recipeId] = {
						"name": title,
						"ingredients": ingredients,
						"instructions": instructions
					}
				else:
					pass
		except Exception as e:
			print(e)
		return recipe