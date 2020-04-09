import re

from nltk import Tree

from lexicon import lex

# TODO: add a duplicate key error for the tree dict; as the second key will just overwrite the first which will lead to unwanted results
#       - this is not possible with dicts, but can be accomplished with a dataframe (such that the len of a column must be equal to the set of its values)
#       - would also allow for the rules and the types to be contained in the same object
#       - but this involves redesigning all the functions to work with dfs instead of dicts
# TODO: make nodes have subscripts (important for traces) while still being able to look up their unsubscripted version in the lexicon
# TODO: make the replacement operation case insensitive
# TODO: regex for adding the super- and subscripts (right now, there'd be a conflict if both "essen" and "gegessen" were in the same sentence)
# TODO: check for traces that are not specified as $t$ (e.g. raise when t follows a dot and then there's a space)


class TernaryBranchingError(Exception):
    """Raise when a mother node contains more than two daughters."""


class TreeStructureError(Exception):
    """Raise when non-terminal daughter node is not specified as a mother in the tree structure."""


class LexiconError(Exception):
    """Raise when a terminal node is not specified in the lexicon."""


class CompositionError(Exception):
    """Raise when a node requires an illicit application of a compositional rule."""


class TreeBracketError(Exception):
    """Raise when a square bracket is directly next to a non-whitespace character (a configuration that gives tikz qtree trouble)."""


class LaTeXEscapeError(Exception):
    """Raise when LaTeX code was not properly escaped in the input string"""


def clean_tree(string, top_node=True):
    """Take a LaTeX qtree string and convert it into a format that is easily usable by nltk for parsing. Return the reformatted string.
    
    Arguments:
        string {str} -- LaTeX qtree string; e.g., "[.\\node(top){NP }; [.AP schuldiger ] [.N Idiot ] ]"
    
    Returns:
        str -- Reformatted string for nltk Tree parsing; e.g., "(NP  (AP schuldiger ) (N Idiot ) )
    """
    # check if \node was escaped or not
    if "\node" in string:
        raise LaTeXEscapeError(f"Slashes in LaTeX qtree string need to be escaped.")
    # replace some characters to make the tree nltk parseable
    string = string.replace("[", "(").replace(".", "").replace("]", ")")
    if top_node:
        string = (
            string.replace("\\node(top){", "").replace("}", "", 1).replace(";", "", 1)
        )

    return string


def find_hierarchy(string):
    """Take a LaTeX qtree string and parse it using nltk. Return a dictionary with (non-terminal) mothers as keys and a list of their daughter(s) as values.
    
    Arguments:
        string {str} -- (reformatted) LaTeX qtree tree string; e.g., "(NP  (AP schuldiger ) (N Idiot ) )
    
    Returns:
        tupl -- (i) nltk.Tree and (ii) Dictionary with mothers and their daughters; e.g., {'NP': ['AP', 'N'], 'AP': ['schuldiger'], 'N': ['Idiot']}
    """
    # perform some cleaning and preparatory steps
    string = clean_tree(string)
    # parse the tree string and turn it into a Tree
    tree = Tree.fromstring(string)
    tree_dict = {}
    daughters = []
    # loop over all the subtrees
    for subtree in tree.subtrees():
        # and get the indices for both daughters
        for i in range(2):
            try:
                # if a node has two daughters, add both
                daughters.append(subtree[i].label())
            except AttributeError:
                # if the subtree is a str, just add that one
                daughters.append(subtree[i])
            except IndexError:
                # to catch nodes with only a single daughter
                pass
        # add the mother and her (list of) daughters
        tree_dict[subtree.label()] = daughters
        daughters = []

    return tree, tree_dict


def check_tree(tree_dict):
    """Check the tree dictionary. Return True of checks are passed.
    
    Arguments:
        tree_dict {dict} -- Hierarchical dictionary of the parsed tree; e.g., {'NP': ['AP', 'N'], 'AP': ['schuldiger'], 'N': ['Idiot']}
    
    Returns:
        bool -- True iff checks are passed
    """
    for mother, daughters in tree_dict.items():
        # more than two daughters are not normally composable
        if len(daughters) > 2:
            raise TernaryBranchingError(
                f"Node {mother} has more than two daughters: {daughters}."
            )

        return True


def compose_lexical(tree_dict, lexicon):
    """Starts the typing process of the tree dictionary by checking the lexicon for types. Return dictionary of nodes in the tree as keys and a tuple of daughters and their semantic types as the (list of) values.
    
    Arguments:
        tree_dict {dict} -- Hierarchical dictionary of the parsed tree; e.g., {'NP': ['AP', 'N'], 'AP': ['schuldiger'], 'N': ['Idiot']}
        lexicon {dict} -- Dictionary with types for the lexical entries; e.g. {"<e, t>": ["schuldiger", "Idiot"]}
    
    Returns:
        (dict, dict) -- Two dictionaries, 
                            (i) with semantic types: {'NP': '<e, t>', 'AP': '<e, t>', 'N': '<e, t>', 'schuldiger': '<e, t>', 'Idiot': '<e, t>'} 
                            (ii) with rules: {'NP': 'PM', 'AP': 'NN', 'N': 'NN', 'schuldiger': 'TN_1', 'Idiot': 'TN_1'}
    """

    def terminal_nodes(element):
        # for pronouns and traces
        if lex_dict[element] in ["pron", "trace"]:
            type_dict[element] = "e"
            # entry for the dictionary containing the rules
            rule_dict[element] = "TN_2"
        # indices
        elif lex_dict[element] == "index":
            type_dict[element] = "-"
            rule_dict[element] = "-"
        # all other nodes
        else:
            # get the semantic type from the lexicon and add it to the type dict
            type_dict[element] = lex_dict[element]
            # for contentful types:
            if lex_dict[element]:
                # entry for the dictionary containing the rules; removed AID tag for space purposes
                rule_dict[element] = "TN_1"
            # for ones that do not have a meaning, do put an empty rule of composition (same as with indices)
            else:
                rule_dict[element] = "-"

    # reverse the lexicon to make it more user-friendly
    lex_dict = {}
    for k, v in lexicon.items():
        for x in v:
            lex_dict[x] = k
    # dictionary containing the mothers as keys and their semantic types as values
    type_dict = {}
    # dictionary containing the mothers as keys and the rules leading to their types as values
    rule_dict = {}
    # iterate over all keys and their values in the tree dict
    for mother, daughters in tree_dict.items():
        # add None values for all other nodes first
        type_dict[mother] = None
        rule_dict[mother] = None
    # then deal with the daughters
    for mother, daughters in tree_dict.items():
        # single-daughter nodes first
        if len(daughters) == 1:
            try:
                terminal_nodes(daughters[0])
            except KeyError:
                # if the node is not a mother node in the tree, it's a terminal node that should be specified in the lexicon
                if daughters[0] not in tree_dict:
                    raise LexiconError(
                        f"Terminal node '{daughters[0]}' not in lexicon."
                    )
        # mothers dominating two daughters now
        if len(daughters) == 2:
            # only do anything with two daughters if the lexicon specifies that something is an index or a trace
            for daughter in daughters:
                try:
                    terminal_nodes(daughter)
                # ignore those key that are not specified in the lexion (no need to raise an error here because we do not expect non-terminals to be lexically specified)
                except KeyError:
                    pass

    return type_dict, rule_dict


def compose_non_branching(tree, type_dict, rule_dict):
    """Take a tree, a dictionary of types, and one with rules, and applies Non-Branching Nodes rule in cases where the mother only has a single daughter. Return tuple with enriched type and rule dictionary.
    
    Arguments:
        tree {dict} -- Hierarchical dictionary of the parsed tree; e.g., {'NP': ['AP', 'N'], 'AP': ['schuldiger'], 'N': ['Idiot']}
        type_dict {dict} -- Dictionary containing the semantic types for each mother node; e.g., {'NP': '<e, t>', 'AP': '<e, t>', 'N': '<e, t>', 'schuldiger': '<e, t>', 'Idiot': '<e, t>'}
        rule_dict {dict} -- Dictionary containing the rule that led to the semantic type; e.g. {'NP': 'PM', 'AP': 'NN', 'N': 'NN', 'schuldiger': 'TN_1', 'Idiot': 'TN_1'}
    
    Returns:
        (dict, dict) -- Enriched type_dict and enriched rule_dict
    """
    for mother, daughters in tree.items():
        # try to fill in empty rules and types
        if type_dict[mother] is None:
            # NN only works for mothers with a single daughter
            if len(daughters) == 1:
                # if the daughter is specified in the type dict with a type
                if (sem_type := type_dict[daughters[0]]) is not None:
                    # add that type
                    type_dict[mother] = sem_type
                    # and note that we employed NN to get to that type in the rule dict
                    rule_dict[mother] = "NN"
            # with semantically empty daughters, these can be ignored
            if len(daughters) == 2:
                try:
                    # so we just use the type of the daughter that does have a type
                    if type_dict[daughters[0]] == "" or type_dict[daughters[1]] == "":
                        type_dict[mother] = (
                            type_dict[daughters[0]] or type_dict[daughters[1]]
                        )
                        # and add NN to the rule dict
                        rule_dict[mother] = "NN"
                except KeyError as e:
                    raise TreeStructureError(
                        f"Tree structure not correct, {e} expected but not found as mother in {tree}."
                    )

    return type_dict, rule_dict


def compose_functional(tree, type_dict, rule_dict):
    """Take a tree, type dictionary, and a dictionary of rules and applies Functional Application to all of them. Return tuple with enriched type and rule dictionary.
    
    Arguments:
        tree {dict} -- Hierarchical dictionary of the parsed tree; e.g., {'NP': ['AP', 'N'], 'AP': ['schuldiger'], 'N': ['Idiot']}
        type_dict {dict} -- Dictionary containing the semantic types for each mother node; e.g., {'NP': '<e, t>', 'AP': '<e, t>', 'N': '<e, t>', 'schuldiger': '<e, t>', 'Idiot': '<e, t>'}
        rule_dict {dict} -- Dictionary containing the rule that led to the semantic type; e.g. {'NP': 'PM', 'AP': 'NN', 'N': 'NN', 'schuldiger': 'TN_1', 'Idiot': 'TN_1'}
    
    Returns:
        (dict, dict) -- Enriched type_dict and enriched rule_dict
    """
    # use a disposable dict to iterate over while modifying the original
    for mother, daughters in tree.items():
        # try to fill in the None types
        if not type_dict[mother]:
            # FA only works for nodes with exactly two daughters
            if len(daughters) == 2:
                try:
                    # both daughters should already have a type and be specified in the type dict
                    type_left = type_dict[daughters[0]]
                    type_right = type_dict[daughters[1]]
                # if they are not, the tree structure is wrong
                except KeyError as e:
                    raise TreeStructureError(
                        f"Tree structure not correct, {e} expected but not found as mother in {tree}."
                    )
                # FA only works if both daughters actually do have a type
                if type_left and type_right:
                    # check which one is the function and which one is the argument
                    if type_left in type_right[0 : len(type_left) + 1]:
                        # take only the remaining type after functional application
                        type_dict[mother] = type_right[
                            len(type_left) + 3 : len(type_right) - 1
                        ]
                        rule_dict[mother] = "FA\\shortleftarrow"
                    elif type_right in type_left[0 : len(type_right) + 1]:
                        # take only the remaining type after functional application
                        type_dict[mother] = type_left[
                            len(type_right) + 3 : len(type_left) - 1
                        ]
                        rule_dict[mother] = "FA\\shortrightarrow"

    return type_dict, rule_dict


def compose_pred_abstr(tree, type_dict, rule_dict):
    """Take a tree, type dictionary, and a dictionary of rules and applies Predicate Abstracttion to all of them. Return tuple with enriched type and rule dictionary.
    
    Arguments:
        tree {dict} -- Hierarchical dictionary of the parsed tree; e.g., {'NP': ['AP', 'N'], 'AP': ['schuldiger'], 'N': ['Idiot']}
        type_dict {dict} -- Dictionary containing the semantic types for each mother node; e.g., {'NP': '<e, t>', 'AP': '<e, t>', 'N': '<e, t>', 'schuldiger': '<e, t>', 'Idiot': '<e, t>'}
        rule_dict {dict} -- Dictionary containing the rule that led to the semantic type; e.g. {'NP': 'PM', 'AP': 'NN', 'N': 'NN', 'schuldiger': 'TN_1', 'Idiot': 'TN_1'}
    
    Returns:
        (dict, dict) -- Enriched type_dict and enriched rule_dict
    """
    for mother, daughters in tree.items():
        if not type_dict[mother]:
            # PA only works with two daughters
            if len(daughters) == 2:
                # only do stuff if both daughters are already typed, otherwise wait until later iteration
                if type_dict[daughters[0]] and type_dict[daughters[1]]:
                    # if one of them is empty, use the other one's type and prefix it with "e"
                    if type_dict[daughters[0]] == "-" or type_dict[daughters[1]] == "-":
                        non_empty = (
                            type_dict[daughters[0]]
                            if type_dict[daughters[1]] == "-"
                            else type_dict[daughters[1]]
                        )
                        type_dict[mother] = f"<e, {non_empty}>"
                        # add the rule to the rule dict
                        rule_dict[mother] = "PA"

    return type_dict, rule_dict


def compose_pred_mod(tree, type_dict, rule_dict):
    """Take a tree, type dictionary, and a dictionary of rules and applies Predicate Modification to all of them. Return tuple with enriched type and rule dictionary.
    
    Arguments:
        tree {dict} -- Hierarchical dictionary of the parsed tree; e.g., {'NP': ['AP', 'N'], 'AP': ['schuldiger'], 'N': ['Idiot']}
        type_dict {dict} -- Dictionary containing the semantic types for each mother node; e.g., {'NP': '<e, t>', 'AP': '<e, t>', 'N': '<e, t>', 'schuldiger': '<e, t>', 'Idiot': '<e, t>'}
        rule_dict {dict} -- Dictionary containing the rule that led to the semantic type; e.g. {'NP': 'PM', 'AP': 'NN', 'N': 'NN', 'schuldiger': 'TN_1', 'Idiot': 'TN_1'}
    
    Returns:
        (dict, dict) -- Enriched type_dict and enriched rule_dict
    """
    for mother, daughters in tree.items():
        if not type_dict[mother]:
            # PM only works with two daughters
            if len(daughters) == 2:
                # make sure that neither daughter's semantic type is None
                if (mother_type := type_dict[daughters[0]]) and type_dict[daughters[1]]:
                    # make sure that the types are the same
                    if mother_type == type_dict[daughters[1]]:
                        if mother_type == "<e, t>":
                            # and then just use one of them
                            type_dict[mother] = mother_type
                            # and add the rule to the rule dict
                            rule_dict[mother] = "PM"
                        else:
                            raise CompositionError(
                                f"Pred.Mod. only applies to <e, t> arguments. Got {mother_type}."
                            )

    return type_dict, rule_dict


def compose_all(tree_dict, lex_dict):
    """Take in a (parsed) tree dictionary and a dictionary with lexical nodes and apply all rules of composition until all semantic types have been derived. Return a tuple of dictionaries. Both with mother nodes as keys; the first with semantic types as the values, the second with the rule of composition used to derive that type.
    
    Arguments:
        tree_dict {dict} -- Hierarchical dictionary of the parsed tree; e.g., {'NP': ['AP', 'N'], 'AP': ['schuldiger'], 'N': ['Idiot']}
        lex_dict {dict} -- Dictionary with types for the lexical entries; e.g. {"<e, t>": ["schuldiger", "Idiot"]}
    
    Returns:
        (dict, dict) -- Two dictionaries, first with semantic types, second one with rules of composition
    """
    if check_tree(tree_dict):
        # start by checking the lexicon for the values of terminal nodes
        typed_nodes, rules = compose_lexical(tree_dict, lex_dict)
        counter = 1
        # repeat the rules of composition a number of times until all nodes have a type
        # or raise a composition error
        while None in typed_nodes.values() and None in rules.values():
            # NN: non-branching nodes
            typed_nodes, rules = compose_non_branching(tree_dict, typed_nodes, rules)
            # FA: functional application of function and argument
            typed_nodes, rules = compose_functional(tree_dict, typed_nodes, rules)
            # PA: predicate abstraction with moved element
            typed_nodes, rules = compose_pred_abstr(tree_dict, typed_nodes, rules)
            # PM: predicate modification for two property-type daughters
            typed_nodes, rules = compose_pred_mod(tree_dict, typed_nodes, rules)
            counter += 1
            if counter > 15:
                raise CompositionError(
                    f"Tree structure could not be composed. Could there be a type mismatch?\n{tree_dict}\n{typed_nodes}"
                )
    return typed_nodes, rules


def enrich_tree_types(string, type_dict):
    """Take in a string and the dictionaries produced via composition and return a string that can be used in LaTeX documents (tikz qtree) with types as subscripts.
    
    Arguments:
        string {str} -- Unannotated LaTeX tree string; e.g., "[.\\node(top){NP }; [.AP schuldiger ] [.N Idiot ] ]"
        type_dict {dict} -- Dictionary containing the semantic types for each mother node; e.g., {'NP': '<e, t>', 'AP': '<e, t>', 'N': '<e, t>', 'schuldiger': '<e, t>', 'Idiot': '<e, t>'}
    
    Returns:
        str -- Annotated string
    """
    if re.search("\S\]", string):
        raise TreeBracketError(
            f"Closing square brackets need to be preceeded by white space:\n{string}"
        )
    for mother in type_dict.keys():
        # we need the space after the mother node so that NP isnt targeted by both N and NP
        search_for = f"{mother} "
        if search_for in string:
            # in type mode, annotate the type
            subscript = type_dict[mother]
            # replace the ugly <> with LaTeX expressions for tuples
            subscript = subscript.replace("<", "\langle ").replace(">", r"\rangle")
            # insert more space after the comma
            subscript = subscript.replace(",", ",\,")
            mother_and_type = f"{mother}_{{{subscript}}} "
            # replace the mother node with mother node plus new subscript
            string = string.replace(search_for, mother_and_type)
    return string


def enrich_tree_full(string, type_dict, rule_dict):
    """Take in a string and the dictionaries produced via composition and return a string that can be used in LaTeX documents (tikz qtree) with types as subscripts and rules as superscripts.
     
     Arguments:
         string {str} -- Unannotated LaTeX tree string; e.g., "[.\\node(top){NP }; [.AP schuldiger ] [.N Idiot ] ]"
         type_dict {dict} -- Dictionary containing the semantic types for each mother node; e.g., {'NP': '<e, t>', 'AP': '<e, t>', 'N': '<e, t>', 'schuldiger': '<e, t>', 'Idiot': '<e, t>'}
         rule_dict {dict} -- Dictionary containing the rule that led to the semantic type; e.g. {'NP': 'PM', 'AP': 'NN', 'N': 'NN', 'schuldiger': 'TN_1', 'Idiot': 'TN_1'}
     
     Returns:
         str -- Annotated string
     """
    if re.search("\S\]", string):
        raise TreeBracketError(
            f"Closing square brackets need to be preceeded by white space:\n{string}"
        )

    for mother in type_dict.keys():
        # we need the space after the mother node so that NP isnt targeted by both N and NP
        search_for = f"{mother} "
        if type_dict[mother]:
            # get types
            subscript = type_dict[mother]
            # replace the ugly <> with LaTeX expressions for tuples
            subscript = subscript.replace("<", "\langle ").replace(">", r"\rangle")
            # insert more space after the comma
            subscript = subscript.replace(",", ",\,")
        # for empty types
        else:
            subscript = "-"
        # get rules
        try:
            superscript = rule_dict[mother]
        # this is to handle indices, which do not have a rule associated with them
        except KeyError:
            superscript = "-"
        # put both the rule and the type together (with some added LaTeX)
        mother_and_more = f"{mother}\\,^{{{{\\color{{mygreen}}\\mathtt{{{superscript}}}}}}}_{{{{\\color{{myred}}{subscript}}}}} "
        # replace the mother node with mother node plus new subscript
        string = string.replace(search_for, mother_and_more)

    return string


def tree_to_latex(tree_string, lexicon):
    """Take a LaTeX qtree tree string, a tree structure dictionary, and a lexicon. Perform a compositional analysis and return a string that can be included in LaTeX documents with an example environment consisting of three subexamples: (i) input tree and the (ii) tree with types and rules.

    Arguments:
        tree_string {str} -- Unannotated LaTeX tree string; e.g. "[.\\node(top){NP }; [.AP schuldiger ] [.N Idiot ] ]"
        lexicon {dict} -- Dictionary with types for the lexical entries; e.g. {"<e, t>": ["schuldiger", "Idiot"]}

    Returns:
        str -- gb4e exe environment with two trees: (i) input tree, (ii) tree with semantic types and compositional rules,
    """
    tree, tree_dict = find_hierarchy(tree_string)
    types, rules = compose_all(tree_dict, lexicon)
    # get the semantic types
    typed_tree_string = enrich_tree_types(tree_string, types)
    # tree with semantic types and rules
    both_tree_string = enrich_tree_full(tree_string, types, rules)
    # the sentence is just the terminal nodes of the tree (those not prefixed with a period)
    sentence = " ".join(tree.leaves()) + "."

    # lambda expression that creates a gb4e example with three sub-examples; including the associated environment tags
    make_ex = (
        lambda w, x, y: f"""\\begin{{exe}}
    \\ex {w}
        \\begin{{xlist}}
            \\ex {x}
            \\ex {y}
        \\end{{xlist}}
    \\end{{exe}}\n\n"""
    )

    # lambda expression for the tikz qtree environment
    make_tree = (
        lambda x: f"""\\begin{{tikzpicture}}[baseline=(top.base)]
                    \Tree {x}
                \end{{tikzpicture}}"""
    )

    # return the long string with the two sub-examples
    return make_ex(
        # capitalize the first letter of the sentence
        sentence[0].upper() + sentence[1:],
        make_tree(tree_string),
        # make_tree(typed_tree_string),
        make_tree(both_tree_string),
    )


tree_strings = [
    "[.\\node(top){S }; [.NP^1 [.N^1 Andrew ] ] [.VP [.V hits ] [.NP^2 [.N^2 Mathis ] ] ] ]",
    "[.\\node(top){A }; [.B not [.C [.D [.E [.F [.G tanzt ] ] ] ] [.Peter ] ] ] ]",
    "[.\\node(top){DP }; [.D der ] [.NP [.AP [.A große ] ] [.N$''''$ [.AP^2 [.A^2 verschüchterte ] ] [.N$'''$ [.AP^3 [.A^3 fliegende ] ] [.N$''$ [.N$'$ [.N Wolf ] ] [.PP [.P aus ] [.NP^2 [.N^2 Twilight ] ] ] ] ] ] ] ]",
    "[.\\node(top){S }; [.NP [.N Andrew ] ] [.VP [.V malt ] [.CoordP [.DP^1 [.D^1 den ] [.NP^2 [.N^2 Wolf ] ] ] [.Coord$'$ [.Coord und_{ind} ] [.DP^2 [.D^2 die ] [.NP^3 [.N^3 Blumen ] ] ] ] ] ] ]",
    "[.\\node(top){S }; [.DP [.D a ] [.NP [.N person ] ] ] [.XP [.1 ] [.S$'$ [.Neg not ] [.S$''$ [.NP^2 [.N^2 Bill ] ] [.VP [.V invite ] [.$t$ ] ] ] ] ] ]",
    "[.\\node(top){NP }; [.AP schuldiger ] [.N Idiot ] ]",
    "[.\\node(top){S }; [.S'' [.NP^1 [.Q some ] [.N^1 person ] ] [.VP [.V is ] [.AP [.A sad ] ] ] ] [.DisjP [.Disj or ] [.S' [.NP^2 [.N^2 she ] ] [.VP^2 [.V^2 sleeps ] ] ] ] ]",
    "[.\\node(top){S' }; [.NP^1 [.Q alle ] [.N^1 Blumen ] ] [.XP [.1 ] [.S [.VP [.V beobachtet ] [.$t$ ] ] [.NP^2 [.N^2 Peter ] ] ] ] ]",
    "[.\\node(top){S }; [.NP^1 [.N^1 Peter ] ] [.VP [.V ist ] [.DP [.D ein ] [.NP^2 [.N$''$^2 [.AP [.A fliegender ] ] [.N$'$^2 [.N^2 Junge ] ] ] [.PP [.P aus ] [.NP^3 [.N^3 Nimmerland ] ] ] ] ] ] ]",
    "[.\\node(top){S }; [.NP [.N er ] ] [.VP [.V ist ] [.AP [.A stolz ] [.PP [.P auf ] [.NP^2 [.N^2 Maria ] ] ] ] ] ]",
    "[.\\node(top){S }; [.NP [.Q einige ] [.N' [.AP^1 [.A^1 schnarchende ] ] [.N'' [.N Jungen ] ] ] ] [.VP [.V zwicken ] [.NP^2 [.D die ] [.N'^2 [.AP^2 [.A^2 kleinen ] ] [.N^2 Männer ] ] ] ] ]",
    "[.\\node(top){S }; [.DP^1 [.D^1 der ] [.NP [.N$''$ [.N$'$ [.N Junge ] ] [.CP [.DP^2 der_{RP} ] [.C$'$ [.C wo ] [.S$'$ [.$t$ ] [.VP [.DP^3 [.D^3 die ] [.NP^2 [.N$''$^2 [.N$'$^2 [.N^2 Fee ] ] [.PP [.P aus ] [.DP^4 Nimmerland ] ] ] ] ]  [.V belästigt ] ] ] ] ] ] ] ]  [.VP^2 [.V^2 fliegt ] ] ]",
    "[.\\node(top){WP }; [.DP^2 [.D^2 dem ] [.NP^2 [.N^2 Schüler ] ] ] [.ZP [.2 ] [.XP [.DP^1 [.D^1 das ] [.NP^1 [.N^1 Buch ] ] ] [.YP [.1 ] [.S [.NP^3 [.N^3 Bill ] ] [.VP [.V$'$ [.V gibt ] [.$t$ ] ] [.$t$ ] ] ] ] ] ] ]",
    "[.\\node(top){S$'$ }; [.DP^2 [.D^2 alle ] [.NP^2 [.N^2 Hunde ] ] ] [.XP [.2 ] [.YP [.DP^1 [.D^1 einige ] [.NP^1 [.N^1 Türen ] ] ] [.ZP [.1 ] [.S [.$t$ ] [.VP [.V schließen ] [.$t$ ] ] ] ] ] ] ]",
]

# tutorial = [
#     "[.\\node(top){S }; [.Markus ] [.arbeitet ] ]",
#     "[.\\node(top){S }; [.NP^1 [.N^1 Andrew ] ] [.VP [.V hits ] [.NP^2 [.N^2 Mathis ] ] ] ]",
#     "[.\\node(top){S }; [.NP [.N Andrew ] ] [.VP [.V malt ] [.CoordP [.DP^1 [.D^1 den ] [.NP^2 [.N^2 Wolf ] ] ] [.Coord$'$ [.Coord und_{ind} ] [.DP^2 [.D^2 die ] [.NP^3 [.N^3 Blumen ] ] ] ] ] ] ]",
#     "[.\\node(top){NP }; [.AP schuldiger ] [.N Idiot ] ]",
#     "[.\\node(top){DP }; [.D der ] [.NP [.AP [.A große ] ] [.N$''''$ [.AP^2 [.A^2 verschüchterte ] ] [.N$'''$ [.AP^3 [.A^3 fliegende ] ] [.N$''$ [.N$'$ [.N Wolf ] ] [.PP [.P aus ] [.NP^2 [.N^2 Twilight ] ] ] ] ] ] ] ]",
#     "[.\\node(top){A }; [.B not [.C [.D [.E [.F [.G tanzt ] ] ] ] [.Peter ] ] ] ]",
#     "[.\\node(top){S }; [.NP [.Q einige ] [.N' [.AP^1 [.A^1 schnarchende ] ] [.N'' [.N Jungen ] ] ] ] [.VP [.V zwicken ] [.NP^2 [.D die ] [.N'^2 [.AP^2 [.A^2 kleinen ] ] [.N^2 Männer ] ] ] ] ]",
#     "[.\\node(top){S }; [.S'' [.NP^1 [.Q some ] [.N^1 person ] ] [.VP [.V is ] [.AP [.A sad ] ] ] ] [.DisjP [.Disj or ] [.S' [.NP^2 [.N^2 she ] ] [.VP^2 [.V^2 sleeps ] ] ] ] ]",
# ]

if __name__ == "__main__":
    with open("LaTeX/treeparses.tex", "w") as f:
        for tree_string in tree_strings:
            f.write(tree_to_latex(tree_string, lex))
    # with open("tutorial.tex", "w") as f:
    #     for tree_string in tutorial:
    #         f.write(tree_to_latex(tree_string, lex))
