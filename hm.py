from __future__ import annotations
from dataclasses import dataclass
from antlr4 import *
from hmLexer import hmLexer
from hmParser import hmParser
from hmVisitor import hmVisitor

import streamlit as st
import pandas as pd
import graphviz


class Buit:
    pass


@dataclass
class Node:
    val: str
    tipus: NodeType
    esq: Arbre
    dre: Arbre


Arbre = Node | Buit


@dataclass
class Variable:
    tipus: str


@dataclass
class Constant:
    tipus: str


@dataclass
class Application:
    left: NodeType
    right: NodeType


NodeType = Variable | Constant | Application


# The TreeVisitor, which is used for both creating the tree with node dataclasses and the type table
class TreeVisitor(hmVisitor):
    def __init__(self):
        self.alph = 96
        self.symbols = {}

    def visitRoot(self, ctx):
        call = list(ctx.getChildren())
        for i in call:
            tree = self.visit(i)

        if not isinstance(tree, Buit):
            return self.symbols, tree
        else:
            return self.symbols, Buit()

    def visitTypedec(self, ctx):

        [t, doub, typ] = list(ctx.getChildren())

        val = self.visit(typ)
        self.symbols[t.getText()] = val

    def visitTypeOnly(self, ctx):
        return Constant(ctx.TYP().getText())

    def visitTypeRec(self, ctx):
        typeRec = self.visit(ctx.typ())

        return Application(Constant(ctx.TYP().getText()), typeRec)

    def visitParen(self, ctx):
        [LPAR, expr, RPAR] = list(ctx.getChildren())
        return self.visit(expr)

    def visitAppl(self, ctx):
        [expr1, expr2] = list(ctx.getChildren())
        self.alph += 1
        nTipus = Variable(self.alph)
        self.symbols[self.alph] = nTipus
        return Node('@', nTipus, self.visit(expr1), self.visit(expr2))

    def visitAbstr(self, ctx):
        [abst, ID, arrow, expr] = list(ctx.getChildren())
        self.alph += 1
        nTipus = Variable(self.alph)
        self.symbols[self.alph] = nTipus

        if ID.getText() in self.symbols:
            tp = self.symbols[ID.getText()]
        else:
            self.alph += 1
            tp = Variable(self.alph)
            self.symbols[ID.getText()] = tp

        return Node('λ', nTipus, self.visit(ID), self.visit(expr))

    def visitNumero(self, ctx):
        numero = ctx.NUM()
        if numero.getText() in self.symbols:
            tp = self.symbols[numero.getText()]
        else:
            self.alph += 1
            tp = Variable(self.alph)
            self.symbols[numero.getText()] = tp

        return Node(numero.getText(), tp, Buit(), Buit())

    def visitElem(self, ctx):
        ID = ctx.ID()
        if ID.getText() in self.symbols:
            tp = self.symbols[ID.getText()]
        else:
            self.alph += 1
            tp = Variable(self.alph)
            self.symbols[ID.getText()] = tp

        return Node(ID.getText(), tp, Buit(), Buit())

    def visitSymbol(self, ctx):
        sym = ctx.SYM()
        if sym.getText() in self.symbols:
            tp = self.symbols[sym.getText()]
        else:
            self.alph += 1
            tp = Variable(self.alph)
            self.symbols[sym.getText()] = tp

        return Node(sym.getText(), tp, Buit(), Buit())


# Finds the type of a variable through recursively checking their dataclass
def recursively_find_type(val: NodeType):

    if isinstance(val, Variable):
        return chr(val.tipus)
    elif isinstance(val, Constant):
        return val.tipus
    elif isinstance(val, Application):
        return '(' + recursively_find_type(val.left) + ' -> ' + recursively_find_type(val.right) + ')'


# Procedure for creating the tree with their value and types
def create_tree(node, symbols, typeTable, parent, dot):
    if isinstance(node, Buit):
        return

    ident = str(id(node))

    val = recursively_find_type(node.tipus)

    # We do this for the numbered variables that are yet to be inferred
    if isinstance(val, int):
        val = chr(val)
    else:
        val = str(val)

    dot.node(ident, node.val + '\n' + val)

    if parent:
        dot.edge(parent, ident)
    create_tree(node.esq, symbols, typeTable, ident, dot)
    create_tree(node.dre, symbols, typeTable, ident, dot)


# An inference function specific for applications
def inferTypesAppl(arbre: Arbre, typeTable, inferenceTable):
    if isinstance(arbre, Buit):
        return

    inferTypesAppl(arbre.esq, typeTable, inferenceTable)
    inferTypesAppl(arbre.dre, typeTable, inferenceTable)

    if (arbre.val == '@'):

        if (isinstance(arbre.esq.tipus, Application) and (arbre.esq.tipus.left != arbre.dre.tipus) and
                isinstance(arbre.esq.tipus.left, Constant) and isinstance(arbre.dre.tipus, Constant)):
            st.write('Type error: ' + recursively_find_type(arbre.esq.tipus.left) +
                     ' vs ' + recursively_find_type(arbre.dre.tipus))
            raise Exception()

        elif isinstance(arbre.esq.tipus, Constant):
            st.write('Type error: Application ( _ -> _ ) cannot be a Constant')
            raise Exception()

        if (isinstance(arbre.tipus, Variable)):
            if (not isinstance(arbre.esq.tipus, Variable)):
                inferenceTable[chr(arbre.tipus.tipus)] = arbre.esq.tipus.right
                typeTable[chr(arbre.tipus.tipus)] = arbre.esq.tipus.right
                arbre.tipus = arbre.esq.tipus.right

            else:

                if (arbre.esq.val != '@' and typeTable[arbre.esq.val] != chr(arbre.esq.tipus.tipus)
                        and not isinstance(typeTable[arbre.esq.val], Variable)):

                    arbre.esq.tipus = typeTable[arbre.esq.val]
                    inferenceTable[chr(arbre.tipus.tipus)] = arbre.esq.tipus.right
                    typeTable[chr(arbre.tipus.tipus)] = arbre.esq.tipus.right
                    arbre.tipus = arbre.esq.tipus.right

                else:

                    inferenceTable[arbre.esq.val] = Application(arbre.dre.tipus, arbre.tipus)
                    typeTable[arbre.esq.val] = Application(arbre.dre.tipus, arbre.tipus)
                    arbre.esq.tipus = Application(arbre.dre.tipus, arbre.tipus)

                    inferenceTable[chr(arbre.tipus.tipus)] = typeTable[arbre.esq.val].right
                    typeTable[chr(arbre.tipus.tipus)] = typeTable[arbre.esq.val].right
                    arbre.tipus = typeTable[arbre.esq.val].right

                if (chr(arbre.tipus.tipus) in typeTable and
                        arbre.esq.tipus.right != inferenceTable[chr(arbre.tipus.tipus)]):

                    inferenceTable[chr(arbre.tipus.tipus)] = arbre.esq.tipus.right
                    typeTable[chr(arbre.tipus.tipus)] = arbre.esq.tipus.right
                    arbre.tipus = arbre.esq.tipus.right

        elif (isinstance(arbre.tipus, Constant)):
            if isinstance(arbre.esq.tipus, Variable):
                inferenceTable[chr(arbre.esq.tipus.tipus)] = Application(arbre.dre.tipus, arbre.tipus)
                typeTable[chr(arbre.esq.tipus.tipus)] = Application(arbre.dre.tipus, arbre.tipus)
                arbre.esq.tipus = Application(arbre.dre.tipus, arbre.tipus)

            if isinstance(arbre.esq.tipus.right, Variable):
                inferenceTable[arbre.esq.val].right = arbre.tipus
                typeTable[arbre.esq.val].right = arbre.tipus
                arbre.esq.tipus.right = arbre.tipus

            if isinstance(arbre.dre.tipus, Variable):
                inferenceTable[chr(arbre.dre.tipus.tipus)] = arbre.esq.tipus.right
                typeTable[chr(arbre.dre.tipus.tipus)] = arbre.esq.tipus.right
                arbre.dre.tipus = arbre.esq.tipus.right

        elif (isinstance(arbre.tipus, Application)):

            if isinstance(arbre.esq.tipus, Variable):
                inferenceTable[chr(arbre.esq.tipus.tipus)] = arbre.tipus.left
                typeTable[chr(arbre.esq.tipus.tipus)] = arbre.tipus.left
                arbre.esq.tipus = arbre.tipus.left

            if isinstance(arbre.dre.tipus, Variable):
                inferenceTable[arbre.dre.val] = arbre.tipus.right
                typeTable[arbre.dre.val] = arbre.tipus.right
                arbre.dre.tipus = arbre.tipus.right

        if isinstance(arbre.dre.tipus, Variable):
            if not isinstance(arbre.esq.tipus.left, Variable):
                inferenceTable[chr(arbre.dre.tipus.tipus)] = arbre.esq.tipus.left
                typeTable[arbre.dre.val] = arbre.esq.tipus.left
                arbre.dre.tipus = arbre.esq.tipus.left
            elif isinstance(typeTable[arbre.dre.val], Constant):
                arbre.dre.tipus = typeTable[arbre.dre.val]

        if (isinstance(arbre.esq.tipus.left, Variable) 
        and not isinstance(arbre.dre.tipus, Variable)):
            inferenceTable[arbre.esq.val].left = arbre.dre.tipus
            typeTable[arbre.esq.val].left = arbre.dre.tipus
            arbre.esq.tipus.left = arbre.dre.tipus

        if ((isinstance(arbre.esq.tipus.right, Variable) 
        and not isinstance(arbre.tipus, Variable)) 
        or (arbre.esq.tipus.right != arbre.tipus)):
            typeTable[arbre.esq.val].right = arbre.tipus
            inferenceTable[arbre.esq.val].right = arbre.tipus
            arbre.esq.tipus.right = arbre.tipus

        if (isinstance(arbre.esq.tipus.right, Application) 
            and isinstance(typeTable[arbre.esq.val], Application) 
            and arbre.esq.tipus.right != typeTable[arbre.esq.val].right):
            arbre.esq.tipus.right = typeTable[arbre.esq.val].right

        if (isinstance(arbre.esq.tipus.right, Application) 
            and isinstance(typeTable[arbre.esq.val], Application) 
            and typeTable[arbre.esq.val].right != arbre.tipus):
            arbre.tipus = typeTable[arbre.esq.val].right


# Same as the last one, but with small changes for abstractions
def inferTypesAbs(arbre: Arbre, typeTable, inferenceTable):
    if isinstance(arbre, Buit):
        return

    inferTypesAbs(arbre.esq, typeTable, inferenceTable)
    inferTypesAbs(arbre.dre, typeTable, inferenceTable)

    if (arbre.val == 'λ') and isinstance(arbre.tipus, Variable):

        arbre.esq.tipus = typeTable[arbre.esq.val]

        if not isinstance(arbre.dre.tipus, Variable):
            typeTable[chr(arbre.tipus.tipus)] = Application(arbre.esq.tipus, arbre.dre.tipus)
            inferenceTable[chr(arbre.tipus.tipus)] = Application(arbre.esq.tipus, arbre.dre.tipus)
            arbre.tipus = Application(arbre.esq.tipus, arbre.dre.tipus)


# Creates two tables. One with the types of all the important data, and one that ignores variables ('a' - 'z')
def createTypeTable(symbols):
    newTable = {}
    newTableNoVars = {}

    for key in symbols:
        typ = recursively_find_type(symbols[key])
        if not isinstance(symbols[key], Variable):
            newTableNoVars[key] = typ
        newTable[key] = typ
    return newTable, newTableNoVars


# Makes the last changes to the inference table to complete it
def removeExtras(inferTable):
    if '@' in inferTable:
        typeSwitch = inferTable['@']
        del inferTable['@']

    for i in inferTable:
        if isinstance(inferTable[i], Variable):
            if i == chr(inferTable[i].tipus):
                inferTable[i] = typeSwitch
                if (isinstance(inferTable[i], Application) 
                    and isinstance(inferTable[i].left, Variable)
                    and chr(inferTable[i].left.tipus) in inferTable):
                    inferTable[i].left = inferTable[chr(inferTable[i].left.tipus)]

            else:
                inferTable[i] = inferTable[chr(inferTable[i].tipus)]


# Does the needed calls for parsing the tree as well a creating the type table, inference, etc
def begin_tree():
    lexer = hmLexer(elems)
    token_stream = CommonTokenStream(lexer)
    parser = hmParser(token_stream)
    tree = parser.root()

    if parser.getNumberOfSyntaxErrors() == 0:
        visitor = TreeVisitor()
        symbols, arbre = visitor.visit(tree)

        # We now have the symbol table with constants and applications, as well as variables

        tableVars, tableNoVars = createTypeTable(symbols)

        df = pd.DataFrame.from_dict(
            tableNoVars, orient='index', columns=['Tipus'])

        st.dataframe(df, use_container_width=True)

        if isinstance(arbre, Node):
            dot = graphviz.Graph()
            create_tree(arbre, tableVars, tableNoVars, None, dot)
            st.graphviz_chart(dot)

            # We now must create another tree, this time with the inferred values
            inferenceTable = {}

            try:
                for i in range(4):
                    inferTypesAppl(arbre, tableVars, inferenceTable)
                    inferTypesAbs(arbre, tableVars, inferenceTable)

                removeExtras(inferenceTable)

                inferTable, _ = createTypeTable(inferenceTable)

                df2 = pd.DataFrame.from_dict(
                    inferTable, orient='index', columns=['Tipus inferits'])

                st.dataframe(df2, use_container_width=True)

                dot2 = graphviz.Graph()
                create_tree(arbre, tableVars, tableNoVars, None, dot2)
                st.graphviz_chart(dot2)

                st.write('La expresión es correcta')
            except:
                pass
        else:
            st.write('La expresión es correcta')

    else:
        st.write(str(parser.getNumberOfSyntaxErrors()) + ' errors de sintaxi.')
        print(tree.toStringTree(recog=parser))


st.title('HinHer')
st.subheader('By Rubén Catalán Rua')

elems = input_stream = InputStream(st.text_area(
    'Escribe aquí la expresión', '(+) 2 x'))
if (st.button("Fer")):
    begin_tree()
