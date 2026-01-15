import numpy as np
from collections import Counter
import math

class MyDecisionTree:
    def __init__(self, max_depth=None, min_samples_split=2, max_features=None):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.tree = None
    
    def fit(self, X, y):
        if self.max_features is None:
            self.max_features = int(math.sqrt(X.shape[1]))
        
        self.tree = self._build_tree(X, y, depth=0)
    
    def _gini_impurity(self, y):
        if len(y) == 0:
            return 0
        counts = Counter(y)
        impurity = 1.0
        for label in counts:
            prob = counts[label] / len(y)
            impurity -= prob ** 2
        return impurity
    
    def _best_split(self, X, y):
        best_gain = 0
        best_feature = None
        best_threshold = None
        
        n_features = X.shape[1]
        features = np.random.choice(n_features, self.max_features, replace=False)
        
        for feature_idx in features:
            feature_values = X[:, feature_idx]
            unique_values = np.unique(feature_values)
            
            for threshold in unique_values:
                left_mask = feature_values <= threshold
                right_mask = feature_values > threshold
                
                if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:
                    continue
                
                gini_parent = self._gini_impurity(y)
                gini_left = self._gini_impurity(y[left_mask])
                gini_right = self._gini_impurity(y[right_mask])
                
                n_left = np.sum(left_mask)
                n_right = np.sum(right_mask)
                n_total = n_left + n_right
                
                gini_children = (n_left / n_total) * gini_left + (n_right / n_total) * gini_right
                gain = gini_parent - gini_children
                
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_idx
                    best_threshold = threshold
        
        return best_feature, best_threshold, best_gain
    
    def _build_tree(self, X, y, depth):
        if (len(np.unique(y)) == 1 or 
            len(y) < self.min_samples_split or
            (self.max_depth is not None and depth >= self.max_depth)):
            return Counter(y).most_common(1)[0][0]
        
        feature, threshold, gain = self._best_split(X, y)
        
        if gain == 0:
            return Counter(y).most_common(1)[0][0]
        
        left_mask = X[:, feature] <= threshold
        right_mask = X[:, feature] > threshold
        
        left_subtree = self._build_tree(X[left_mask], y[left_mask], depth + 1)
        right_subtree = self._build_tree(X[right_mask], y[right_mask], depth + 1)
        
        return {
            'feature': feature,
            'threshold': threshold,
            'left': left_subtree,
            'right': right_subtree
        }
    
    def _predict_single(self, x, tree):
        if not isinstance(tree, dict):
            return tree
        
        feature_val = x[tree['feature']]
        if feature_val <= tree['threshold']:
            return self._predict_single(x, tree['left'])
        else:
            return self._predict_single(x, tree['right'])
    
    def predict(self, X):
        return np.array([self._predict_single(x, self.tree) for x in X])
    
    def _predict_proba_single(self, x, tree):
        if not isinstance(tree, dict):
            return {0: 0.0, 1: 1.0} if tree == 1
