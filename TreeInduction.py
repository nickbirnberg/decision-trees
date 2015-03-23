from collections import namedtuple
import re
import json
import math


class DataRow:
    def __init__(self, attribs):
        self.attribs = attribs
        self.tuple = namedtuple('Row', attribs)

    def parse(self, row):
        values = []
        for val in zip(self.attribs, row.split(',')):
            values.append(val[1])
        return self.tuple(*values)


class Tree:
    def __init__(self, attribs, examples, is_leaf):
        self.attribs = attribs
        self.examples = examples
        self.is_leaf = is_leaf


def load():
    with open('testData.arff') as f:
        whole_text = f.read()
        split_data = whole_text.split('@DATA')
        attr_vals = re.findall(r'\{(.+?)\}', split_data[0])
        tree_vals = []
        for values in attr_vals:
            final_vals = values.split(',')
            tree_vals.append(final_vals)
        attributes = re.findall(r"'(\w+)'", split_data[0])

        csv_data = split_data[1].splitlines()
        csv_data.pop(0)
        data_list = []
        for row in csv_data:
            data_tuple = DataRow(attributes)
            typed_row = data_tuple.parse(row)
            data_list.append(typed_row)
        diction = dict(zip(attributes, tree_vals))
        decision_tree = Tree(diction, data_list, 0)
        return decision_tree


def highest_count(decision_tree):
    count = 0
    for ex in decision_tree.examples:
        if ex.Wait == '"Yes"':
            count += 1
        else:
            count -= 1
    if count > 0:
        return "Wait: Yes"
    else:
        return "Wait: No"


def find_best_attr(passed_tree):
    decision_tree = passed_tree
    highest_gain = 0
    best_attribute = 0
    num_attributes = len(decision_tree.attribs) - 1

    for attrib in range(num_attributes):
        gain_val = 1 - gain(decision_tree, decision_tree.attribs.keys()[attrib])
        if gain_val >= highest_gain:
            best_attribute = decision_tree.attribs.keys()[attrib]
            highest_gain = gain_val
    return best_attribute


def gain(passed_tree, test_attribute):
    decision_tree = passed_tree
    attrib = test_attribute
    total_gain = float(0)
    for val in decision_tree.attribs[attrib]:
        new_data = []
        positive = 0
        negative = 0
        for ex in decision_tree.examples:
            if getattr(ex, attrib) == val:
                new_data.append(ex)
                if getattr(ex, "Wait") == '"Yes"':
                    positive += 1
                else:
                    negative += 1
        if negative + positive > 0:
            qval = float(positive) / (negative + positive)
            ent = entropy(qval)

        else:
            ent = 0
        prob = float(len(new_data)) / len(decision_tree.examples)
        total_gain += float((ent * prob))
    return total_gain


def entropy(qval):
    if qval == 0:
        return 0
    if qval == 1:
        return 0
    log1 = math.log(qval, 2)
    log2 = math.log(1 - qval, 2)
    ent = -(qval * log1 + (1 - qval) * log2)
    return ent


def chisquared(passed_tree, test_attrib, temp_attribs):
    decision_tree = passed_tree
    attrib = test_attrib
    attrib_data = temp_attribs
    num_pos = 0
    num_neg = 0
    delta = 0
    compare = 0
    print decision_tree.examples
    print attrib
    df = len(attrib_data[attrib]) - 1
    if df == 1:
        compare = 2.706
    if df == 2:
        compare = 4.605
    if df == 3:
        compare = 6.251
    for text_ex in decision_tree.examples:
        if text_ex.Wait == '"Yes"':
            num_pos += 1
        else:
            num_neg += 1
    for val in attrib_data[attrib]:
        new_data = []
        positive = 0
        negative = 0
        for ex in decision_tree.examples:
            if getattr(ex, attrib) == val:
                new_data.append(ex)
                if getattr(ex, "Wait") == '"Yes"':
                    positive += 1
                else:
                    negative += 1
        pos_hat = num_pos * ((positive + negative) / float(num_pos + num_neg))
        neg_hat = num_neg * ((positive + negative) / float(num_pos + num_neg))
        delta += (math.pow(positive - pos_hat, 2) / pos_hat) + (math.pow(negative - neg_hat, 2) / neg_hat)
        print 'delta=', delta
    print delta
    print compare
    return delta >= compare


def induction(passed_tree):
    decision_tree = passed_tree

    class_check = [x[-1] for x in decision_tree.examples]
    if len(class_check) - 1 <= 0:
        passed_tree.isLeaf = 1
        return highest_count(decision_tree)
    elif class_check.count(class_check[0]) == len(class_check):
        passed_tree.isLeaf = 1
        return class_check[0]
    else:
        passed_tree.isLeaf = 0
        subtrees = []
        best_attr = find_best_attr(decision_tree)
        temp_attribs = decision_tree.attribs.copy()
        del (decision_tree.attribs[best_attr])
        return_tree = {best_attr: {}}
        for val in temp_attribs[best_attr]:
            new_data = []
            for ex in decision_tree.examples:
                if getattr(ex, best_attr) == val:
                    new_data.append(ex)

            temp_tree = Tree(decision_tree.attribs, new_data, 0)
            subtrees.append(temp_tree)
            return_tree[best_attr][val] = induction(temp_tree)
        if all([sub.isLeaf == 1 for sub in subtrees]):
            print
            if not chisquared(decision_tree, best_attr, temp_attribs):
                print 'alsoran'
                return {best_attr: highest_count(decision_tree)}
        return return_tree


tree = load()

induced = induction(tree)

print json.dumps(induced, indent=4)