[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Automatic Generation of Type-and-Rule-Annotated qtree Trees with Python

The script is a very simple program that parses LaTeX [TikZ qtree](https://ctan.org/pkg/tikz-qtree?lang=en)<sup id="a1">[1](#f1)</sup> strings and outputs the same tree annotated with semantic types and the rules of composition (Heim-&-Kratzer-style) that led to that type. Being simple, the script comes with a number of restrictions some of which I'll detail below. 

As an aside, my implementation is the offspring of a desire to program, rather than one to innovate. There are certainly better and more thought-out alternatives around.

<b id="f1">1</b> For TikZ itself, see https://www.ctan.org/pkg/pgf. [↩](#a1)

## Getting Started

```python
# lexicon that includes the semantic types
lex = {"e": ["Andrew", "Mathis"], "<e, t>": ["hits"]}

# define the tree that is to be annotated
tree_string = "[.\\node(top){S }; [.NP^1 [.N^1 Andrew ] ] [.VP [.V hits ] [.NP^2 [.N^2 Mathis ] ] ] ]"

# save the output to a LaTeX file
with open("LaTeX/treeparses.tex", "w") as f:
    f.write(tree_to_latex(tree_string, lex))
```

## Examples

### Single Image

The input string in (1) produces the output below (once the corresponding (Xe)LaTeX code is compiled to pdf).

1. `[.\\node(top){S }; [.NP^1 [.N^1 Andrew ] ] [.VP [.V hits ] [.NP^2 [.N^2 Mathis ] ] ] ]`

<p align="center">
<img src="https://github.com/mkthalmann/rule-and-type-parse/blob/master/media/sample.jpg" width="448" height="490">
</p>

### Multipage PDF

<p align="center">
<img src="https://github.com/mkthalmann/rule-and-type-parse/blob/master/media/semtree.gif" width="800">
</p>

## Restrictions

* Nodes labels in the tree need to be unique:
  * `[.S [.NP [.N Peter ] ] [.VP [.V watched ] [.NP [.N TV ] ] ] ]` would be illicit because both `NP` and `N` occur twice.
* Lexical entries and the nodes corresponding to them must match exactly: the look-up is case sensitive and does not recognize inflectional suffixes or the like (rectifying this would probably involve tokenizing, something I have not done before).
* Traces cannot bear indices; though that is easily fixed. I just haven't had a reason to do so yet.

## License

<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.

## Feedback

If you have any comments, feature requests or suggestions, please feel free to send me an [e-mail](mailto:maik.thalmann@gmail.com?subject=[GitHub]%20SemTrees).
