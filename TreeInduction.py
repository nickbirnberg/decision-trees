import math


class ARFFReader:
    def __init__(self, file_name):
        self._read_file(open(file_name, 'r'))

    def _read_file(self, lines_iterator):
        """
        This will return the file
        :param lines_iterator:
        """
        attributes = {}
        attribute_names = []
        # Parse each attribute into a Attribute => Values dictionary.
        for line in lines_iterator:
            # ARFF Comments
            if line.startswith('%'):
                continue

            # ARFF Attributes
            if line.lower().startswith('@attribute'):
                space_separated = line.split(' ', 2)
                name = space_separated[1].strip()
                attribute_names.append(name)
                fields = space_separated[2].strip('{}\n\r ')

                fields = [field.strip(' \n\r"') for field in fields.split(',')]

                attributes[name] = fields

            # Break so that we can parse data.
            if line.lower().startswith('@data'):
                break
        self.attributes = attributes
        # Store data in list of Attribute => Value dictionaries.
        examples = []
        for line in lines_iterator:
            # ARFF Comments
            if line.startswith('%'):
                continue
            data_dict = {}
            for index, value in enumerate(line.split(',')):
                data_dict[attribute_names[index]] = value.strip()
            examples.append(data_dict)
        self.examples = examples


class DecisionNode:
    """
    Holds an attribute, as well as the number of positive
    and negative examples at the node.
    Has other DecisionNodes or DecisionResults as children
    for each value of the attribute.
    """
    def __init__(self, attribute, num_pos, num_neg):
        self.branches = {}
        self.attribute = attribute
        self.num_pos = num_pos
        self.num_neg = num_neg

    def add_branch(self, value, subtree):
        self.branches[value] = subtree

    def display(self, indent=0):
        print self.attribute + '?'
        for (value, subtree) in self.branches.iteritems():
            print ' ' * 4 * indent, value, '==>',
            subtree.display(indent + 1), '\n'

    def has_only_leafs(self):
        for subtree in self.branches.itervalues():
            if isinstance(subtree, DecisionNode):
                return False
        return True


class DecisionResult:
    """
    Holds a decision (yes/no), as well as the number of positive
    and negative examples that went into the decision.
    """

    def __init__(self, (result, num_pos, num_neg)):
        self.result = result
        self.num_pos = num_pos
        self.num_neg = num_neg

    # noinspection PyUnusedLocal
    def display(self, indent=None):
        print "Result = " + self.result


def decision_tree_learning(examples, attributes, parent_examples):
    example_classes = [example[DECISION_ATTRIBUTE] for example in examples]
    # if examples is empty then return PLURALITY-VALUE(parent examples)
    if not examples:
        return DecisionResult(plurality_value(parent_examples))
    # else if all examples have the same classification then return the classification
    elif len(set(example_classes)) == 1:
        return DecisionResult(plurality_value(examples))
    # else if attributes is empty then return PLURALITY-VALUE(examples)
    elif not attributes:
        return DecisionResult(plurality_value(examples))
    else:
        # A <- argmax in attributes IMPORTANCE(a, examples)
        best_attr, num_pos, num_neg = find_best_attr(attributes, examples)
        # tree <- a new decision tree with root test A
        tree = DecisionNode(best_attr, num_pos, num_neg)
        # for each value vk of A do
        for value in attributes[best_attr]:
            # exs <- {e : e in examples and e.A = vk}
            new_examples = []
            for example in examples:
                if example[best_attr] == value:
                    new_examples.append(example)
            new_attributes = dict(attributes)
            del new_attributes[best_attr]
            subtree = decision_tree_learning(new_examples, new_attributes, examples)
            tree.add_branch(value, subtree)
        return tree


def find_best_attr(attributes, examples):
    """
    pick the attribute that goes as far as possible toward providing an exact classification of the examples
    :param attributes: List of attributes to check.
    :param examples: List of examples in data set.
    :return: best attribute
    """
    highest_gain = 0
    best_num_pos = 0
    best_num_neg = 0
    best_attribute = None

    for attribute, values in attributes.iteritems():
        gain_val, num_pos, num_neg = gain(attribute, values, examples)
        if gain_val >= highest_gain:
            best_attribute = attribute
            highest_gain = gain_val
            best_num_pos = num_pos
            best_num_neg = num_neg
    return best_attribute, best_num_pos, best_num_neg


def gain(attribute, values, examples):
    """
    Calculates gain.
    :param attribute: Attribute to calculate gain on.
    :param values: All possible values of the attribute.
    :param examples: List of examples in data set.
    :return: Gain of attribute.
    """
    total_gain = float(0)
    num_pos = 0
    num_neg = 0
    for value in values:
        positive = 0
        negative = 0
        for example in examples:
            if example[attribute] == value:
                if example[DECISION_ATTRIBUTE] == DECISION_VALUES[0]:
                    positive += 1
                else:
                    negative += 1
        if negative + positive > 0:
            qval = float(positive) / (negative + positive)
            ent = entropy(qval)
        else:
            ent = 0
        prob = float(positive + negative) / len(examples)
        total_gain += float(ent * prob)
        num_pos += positive
        num_neg += negative
    return 1 - total_gain, num_pos, num_neg


def plurality_value(examples):
    """
    :param examples: Current set of examples passed in.
    :return: Tuple containing decision, and number of
            positive/negative examples
            Decision is random if there's an equal amount.
    """
    num_pos = 0
    num_neg = 0
    for example in examples:
        if example[DECISION_ATTRIBUTE] == DECISION_VALUES[0]:
            num_pos += 1
        else:
            num_neg += 1
    if num_pos > num_neg:
        return "Yes", num_pos, num_neg
    elif num_pos < num_neg:
        return "No", num_pos, num_neg
    else:
        import random
        random_int = random.randint(1, 2)
        if random_int == 1:
            return "Yes", num_pos, num_neg
        else:
            return "No", num_pos, num_neg


def entropy(q_val):
    if q_val == 0:
        return 0
    if q_val == 1:
        return 0
    log1 = math.log(q_val, 2)
    log2 = math.log(1 - q_val, 2)
    ent = -(q_val * log1 + (1 - q_val) * log2)
    return ent


def prune(d_tree, attributes):
    """
    Recursively prunes tree from bottom up.... after going top->down
    :param d_tree: node to be pruned
    :param attributes: List of attributes in dataset. Only needed to calculate
                       degrees of freedom in chi-squared test.
    :return: pruned tree
    """
    if d_tree.has_only_leafs():
        if reject_null_hypothesis(d_tree, attributes):
            if d_tree.num_pos > d_tree.num_neg:
                return DecisionResult(("Yes", d_tree.num_pos, d_tree.num_neg))
            else:
                return DecisionResult(("No", d_tree.num_pos, d_tree.num_neg))
        else:
            return d_tree
    else:
        # Recurse onto children DecisionNodes
        for label, subtree in d_tree.branches.iteritems():
            if isinstance(subtree, DecisionNode):
                d_tree.branches[label] = prune(subtree, attributes)
    return d_tree


def reject_null_hypothesis(tree_node, attributes):
    from scipy.stats import chi2

    total_pos = tree_node.num_pos
    total_neg = tree_node.num_neg
    # Calculate the value that Delta would reject at 5% level
    df = len(attributes[tree_node.attribute]) - 1
    compare = chi2.ppf(.95, df)
    delta = 0
    for decision in tree_node.branches.itervalues():
        value_pos = decision.num_pos
        value_neg = decision.num_neg
        pos_hat = total_pos * ((value_pos + value_neg) / float(total_pos + total_neg))
        neg_hat = total_neg * ((value_pos + value_neg) / float(total_pos + total_neg))
        delta += (math.pow(value_pos - pos_hat, 2) / pos_hat) + (math.pow(value_neg - neg_hat, 2) / neg_hat)
    return delta >= compare


if __name__ == '__main__':
    # Read ARFF file. Current reader only supports attributes with discrete domains.
    read_arff = ARFFReader('testData.arff')

    # Choose attribute to form decision on.
    DECISION_ATTRIBUTE = 'will_wait'
    DECISION_VALUES = read_arff.attributes[DECISION_ATTRIBUTE]

    del read_arff.attributes[DECISION_ATTRIBUTE]

    # Create decision tree.
    decision_tree = decision_tree_learning(read_arff.examples, read_arff.attributes, None)
    decision_tree.display()

    # Prune decision tree:
    pruned_tree = decision_tree
    number_of_prune_iterations = 1
    for i in range(0, number_of_prune_iterations):
        pruned_tree = prune(pruned_tree, read_arff.attributes)
    # Print pruned tree
    print '\n\n#######\nPruned Tree:\n#######\n\n'
    pruned_tree.display()