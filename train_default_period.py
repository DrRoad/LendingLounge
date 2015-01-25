import pandas as pd
import numpy as np
import glob, sys
from datetime import date
import pickle
from random import randint
import time
import json
import os
from datetime import datetime

from sklearn.cross_validation import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor 
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVR
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

import data_manipulation as dm

class Trainer():

	def __init__(self):
		self.load_data()

	def load_data(self):
		f = open('mysql_dump.pickle', 'rb')
		self.loanData = pickle.load(f)
		self.loanData = pd.DataFrame(self.loanData)

	def drop_na(self):
		self.loanData = loanData.dropna()
		self.loanData.index = range(len(self.loanData))

	def drop_columns(self):
		#drop the columns with malformed data in mysql db
		self.loanData = self.loanData.drop(['none',
											'educational',
											'IA',
											'IDAHO',
											'ME',
											'NE',
											'other_housing',
											'issue_year'], 1)

	def drop_prepaid_loans(self):
		indices_to_drop = []
		for i in range(len(self.loanData)):
			if self.loanData['loan_status'][i]==1 and self.loanData['days_to_zero_dollars'][i] < 1000:
				indices_to_drop.append(i)
		self.loanData = self.loanData.drop(indices_to_drop, 0)
		print "Number of prepaid loans: ", len(indices_to_drop)
		print "Number of loans after dropping prepaids: ", len(self.loanData)

	def define_features_targets(self, kind="regression"):
		self.features = self.loanData.drop(['loan_status', 
											'days_to_zero_dollars'], 1)
	
		self.features = self.features.values
		#choose different target variables for regression vs classification
		if kind == "regression":
			self.targets = self.loanData['days_to_zero_dollars'].values
		elif kind == "classification":
			self.targets = self.loanData['loan_status'].values

	def preprocess(self):
		(self.X_train, 
		 self.X_test, 
		 self.y_train, 
		 self.y_test) = dm.split_train_test(features=self.features, 
		 									targets=self.targets, 
		 									test_size=0.01)
		(self.X_train, self.X_test) = dm.standardize_samples(self.X_train, 
														  self.X_test)
		
		(self.X_train, self.X_test) = dm.scale_samples_to_range(self.X_train, 
																self.X_test)

	def define_rfr(self, n_estimators=10):
		self.regr = RandomForestRegressor(n_estimators=n_estimators, oob_score=True)
		print self.regr.get_params()

	def define_linear_regressor(self):
		self.regr = LinearRegression()
		print self.regr.get_params()

	def define_SVR(self, C=1, gamma=0.1):
		self.regr = SVR(C=C, gamma=gamma, verbose=3)
		print self.regr.get_params()

	def define_rfc(self, n_estimators=10):
		self.clf = RandomForestClassifier(n_estimators=n_estimators, oob_score=True)
		print self.clf.get_params()

	def train(self, kind="regression"):
		print "Fitting training data"
		if kind == "regression":
			self.regr.fit(self.X_train, self.y_train)
		elif kind == "classification":
			self.clf.fit(self.X_train, self.y_train)

	def predict(self, X, kind="regression"):
		if kind == "regression":
			self.prediction = self.regr.predict(X)
		elif kind == "classification":
			self.prediction = self.clf.predict(X)

	def score(self, X, y, kind="regression"):
		if kind == "regression":
			score_val = self.regr.score(X, y)
			print "R2 Score: ", score_val
		elif kind == "classification":
			score_val = self.clf.score(X, y)
			print "Accuracy: ", score_val
			print classification_report(y, self.prediction)

	def run_pca(self, n_components=20):
		self.pca = PCA(n_components=n_components)
		self.X_train = self.pca.fit_transform(self.X_train)
		print "Reduced data down to ", self.pca.n_components_, " dimensions: "
		print "Transforming test data ..."
		self.X_test = self.pca.transform(self.X_test)

	def plot_prediction(self):
		plt.scatter(self.prediction, self.y_test)
		plt.xlabel('prediction')
		plt.ylabel('y_test')
		plt.show()

	def runSVRGridSearch(self):
		C_vals = [0.01, 0.1, 1, 10, 100]
		gamma_vals = [1E-2, 1E-1, 1, 1E1, 1E2, 1E3, 1E4]

		for C in C_vals:
			for gamma in gamma_vals:
				print "\n\n C: ", C, "  gamma: ", gamma
				self.define_SVR(C=C, gamma=gamma)
				self.train()
				print "Training Scores:"
				self.predict(self.X_train)
				self.score(self.X_train, self.y_train)
				print "Testing Scores:"
				self.predict(self.X_test)
				self.score(self.X_test, self.y_test)

	def pickle_algo(self, fileName, kind="regression"):
		print "pickling algorithm"
		if kind == "regression":
			f = open(fileName, 'wb')
			pickle.dump(self.regr, f)
			f.close()
		elif kind == "classification":
			f = open(fileName, 'wb')
			pickle.dump(self.clf, f)
			f.close()


for iteration in range(10):
	#Run regression
	trainer = Trainer()
	trainer.drop_columns()
	trainer.drop_prepaid_loans()
	trainer.define_features_targets()
	trainer.preprocess()
	trainer.define_rfr(n_estimators=100)
	trainer.train()
	print "Training Scores"
	trainer.predict(trainer.X_train)
	trainer.score(trainer.X_train, trainer.y_train)
	print "Test Scores"
	trainer.predict(trainer.X_test)
	trainer.score(trainer.X_test, trainer.y_test)
	print "Feature Importances"
	feature_importances = trainer.regr.feature_importances_
	for i, f in enumerate(feature_importances):
		print trainer.loanData.drop(['loan_status'], 1).columns[i], f
	print "oob score"
	print trainer.regr.oob_score_
	fileName = './pickles/rfr_%s.pickle' %iteration
	trainer.pickle_algo(fileName=fileName, kind="regression")


	#Run Clasification
	trainer = Trainer()
	trainer.drop_columns()
	trainer.drop_prepaid_loans()
	trainer.define_features_targets(kind="classification")
	trainer.preprocess()
	trainer.define_rfc(n_estimators=100)
	trainer.train(kind="classification")
	print "Training Scores"
	trainer.predict(trainer.X_train, kind="classification")
	trainer.score(trainer.X_train, trainer.y_train, kind="classification")
	print "Test Scores"
	trainer.predict(trainer.X_test, kind="classification")
	trainer.score(trainer.X_test, trainer.y_test, kind="classification")
	print "Feature Importances"
	feature_importances = trainer.clf.feature_importances_
	for i, f in enumerate(feature_importances):
		print trainer.loanData.drop(['loan_status'], 1).columns[i], f
	print "oob score"
	print trainer.clf.oob_score_
	fileName = './pickles/rfc_%s.pickle' %iteration
	trainer.pickle_algo(fileName=fileName, kind="classification")

