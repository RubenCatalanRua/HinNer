# Analitzador de tipus HinHer

## Introducció

L'analitzador HinHer aplica l'algoritme Hindley-Milner per fer inferència de tipus d'una expressió en base a definicions de tipus i la pròpia expressió.


## Com utilitzar l'analitzador


### Dependències

Per poder fer ús de l'analitzador sense problemes, es necessari tenir instal·lat al teu sistema:

* Python 3.10 o superior (pels tipus algebraics)
* ANTLR4
```console
	pip install antlr4-tools
	pip install antlr4-python3-runtime
```
* Dataclasses y future (pels dataclass)
```console
	pip install dataclasses
	pip install future
```
* Streamlit (per visualitzar l'analitzador)
```console
	pip install streamlit
```
* Pandas (per les taules)
```console
	pip install pandas
```
* Graphviz (pels grafs en dot language)
```console
	pip install graphviz
```

### Execució

Havent realitzat les instal·lacions pertinents, però abans de fer ús de l'analitzador, s'han de crear els fitxers necessaris a partir de la gramàtica. En un directori amb els arxius <b>hm.g4</b> i <b>hm.py</b> escrivim per terminal:

```console
antlr4 -Dlanguage=Python3 -no-listener -visitor hm.g4
```

Després, executem la següent comanda:

```console
streamlit run hm.py
```

Se'ns obrirà una finestra de streamlit on tindrem una capsa de text. Seguint les indicacions de la gramàtica, podem escriure, línea per línea, una declaració de tipus. L'última línea ha de ser la expressió que volem inferir. Alternativament es pot escriure nomès declaracions de tipus. 

Si tot el text a la capsa es correcte, en premer al botó <b>Fer</b>, veurem per pantalla en una taula, primerament els tipus declarats i l'arbre inicial, sense inferències. Desprès les variables inferides i per últim, l'arbre amb les inferències afegides. Podem canviar les declaracions i expressió sempre que vulguem, i veure el nou arbre prement de nou el botó.

Si hi han errors de sintaxi, nomès veurem un missatge que ho indicarà. Si, per contra, hi ha un error de tipus que no permet realitzar la inferència, nomès veurem l'arbre inicial i un missatge que mostrarà les declaracions en conflicte. Alternativament, pot haver un error en el tipus de l'aplicació (si aquest es una constant N, per exemple), i es mostrarà per pantalla l'error pertinent.


## La gramàtica

S'ha optat per utilitzar una gramàtica senzilla però funcional. Reconeix un nombre arbitrari de declaracions de tipus i després, opcionalment, la expressió.

Els tipus es llegeixen com lletres en majúscula, mentre que les variables, com a lletres en minúscula.

Exemple de entrada válida:

1 :: N

(+) :: N -> N -> N

\x -> (+) 1 x

L'analitzador accepta aquestes entrades en una mateixa línea, però es recomanable deixar cadascuna en una línea per millor enteniment.

Els tipus declarats son valors (números o operadors bàsics entre parèntesi), seguits de '::' i després el seu tipus, amb lletres en majúscula. Per últim, la expressió va al final de les declaracions de tipus.


## Decisions de disseny

Com ja s'ha explicat, es guarden les declaracions de tipus en un diccionari. Les declaracions es guarden en tres dataclasses distintes:

* <b>Variable</b> : Per a Nodes dels quals encara no sabem el tipus (s'ha d'inferir). S'assignen valors de la 'a' a la 'z'
* <b>Constant</b> : Per a termes declarats on nomès tenim un tipus (2 :: N, 3 :: X)
* <b>Aplicació</b> : Per a termes amb més d'un tipus ((+) :: N -> N -> N)

Afegim també un tipus algebraic <em>NodeType</em>, que pot ser qualsevol dels dataclasses mencionats.

Pels AST, he decidit fer una dataclass <b>Node</b>, que conté quatre paràmetres:

* <b>val</b> : string amb el 'valor' del node (2, (-), @, etc.)
* <b>tipus</b> : NodeType que recull el tipus del node
* <b> esq</b> : el subarbre esquerre del node, referenciat amb un tipus algebraic <em>Arbre</em>, que pot ser o un Node, o Buit (no hi ha res).
* <b>dre</b> : similar a <b>esq</b> pero pel subarbre dret.


Els tipus declarats es guarden en un diccionari valor - tipus anomenat _typeTable_, on valor pot ser qualsevol símbol declarat inicialment. 

En un altre diccionari anomenat _inferenceTable_, també de valor - tipus, guardem els tipus inferits durant l'algorisme Hindley-Milner.

## Com es fa la inferència

És llegeixen les declaracions de tipus, i s'afegeixen a un diccionari, on la clau es el símbol (pot ser un número, operador, etc) i el valor es un dataclass. És realitzarà un parseig de la expressió per crear l'arbre i anar guardant variables que hauran de ser inferides dins el diccionari.

Per pantalla es mostrarà el arbre inicial i, posteriorment, mitjançant l'algorisme de Hindley-Milner, es realitza la inferència de les aplicacions i després les abstraccions.

L'analitzador intentarà realitzar tota la inferència si es possible. He escollit un for loop que fa quatre crides a la funció de inferència d'aplicacions, on realitza petits canvis a cada pasada fins completar totes les possibles transformacions. Posteriormentent, la inferència serà completada per la funció inferència d'abstraccions (si n'hi ha). He trobat que amb una sola pasada a aquesta funció ja n'hi havia suficient.

## Casos de prova

El codi passa els jocs de proves mostrats a la descripció de la pràctica, així com el cas del punt esborrat __7a1__, si bé, amb tipus definits (en majúscula).

Gràcies a que el algorisme no requereix explicitament de posar els tipus de tots els operadors, podem realitzar inferències completes si això es possible. Per exemple:

+ 2 :: N
+ (+) 2 ((+) x x)

L'algorisme pot completar tots els tipus no inferits gràcies a les múltiples passades que realitza per l'arbre, arribant al tipus de l'expressió completa.