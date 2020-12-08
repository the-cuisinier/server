from django.shortcuts import render
import json
import firebase_admin
from firebase_admin import credentials, firestore
from django.http import HttpResponse, JsonResponse

# Create your views here.


def checkStringHamptonPercent(str1, str2):
	i = 0
	count = 0

	while(i < min(len(str1), len(str2))):
		if(str1[i] != str2[i]):
			count += 1
		i += 1
	return count / min(len(str1), len(str2))


def getRecipe(data, ingredients):
	count = 0
	dish = data.to_dict()
	listOfRecipes = {}
	po = None
	for ingr in ingredients:
		if "materials" in dish.keys():
			det = dish["materials"]
			for key in det.keys():
				if checkStringHamptonPercent(ingr, key) <= 0.12:
					po = key
					listOfRecipes[data.id] = listOfRecipes.get(data.id, 0) + 1
	if len(listOfRecipes.keys()) == 0:
		return False, [], po
	else:
		return True, listOfRecipes, po


def home(request):
	if request.method == 'POST':
		requestBody = json.loads(request.body)
		cred = credentials.Certificate("./credentials.json")
		firebase_admin.initialize_app(cred)
		db = firestore.client()
		uid = requestBody["uid"]
		user_ref = db.collection(u"inventory").document(uid)
		fridgeDetails = user_ref.get().to_dict()
		doc_ref = db.collection(u'recipes')
		docs = doc_ref.stream()
		data = {}
		for i in docs:
			isResult, recipeMap, po = getRecipe(i, fridgeDetails.keys())
			if isResult:
				for key in recipeMap.keys():
					data[key] = data.get(key, 0) + recipeMap[key]

		dishes = []
		data["message"] = True
		return JsonResponse(data)
	else:
		data = {
			"message": False
		}
		return JsonResponse(data)