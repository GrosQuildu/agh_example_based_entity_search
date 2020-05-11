## Implementation of "Example Based Entity Search in the Web of Data".

```bibtex
@inproceedings{inproceedings,
    author = {Bron, Marc and Balog, Krisztian and Rijke, Maarten},
    year = {2013},
    month = {03},
    pages = {392-403},
    title = {Example Based Entity Search in the Web of Data},
    volume = {7814},
    isbn = {9783642369728},
    doi = {10.1007/978-3-642-36973-5_33}
}
```

## This tool

This tool solves a problem of searching relevant entities in [Linked Open Data](https://lod-cloud.net) (structured) graphs.

Problem statement: given relation (plain text query like "astronauts who walked on the Moon") and set of examples
(like [&lt;http://dbpedia.org/resource/Neil_Armstrong&gt;](http://dbpedia.org/resource/Neil_Armstrong) and
[&lt;http://dbpedia.org/resource/Alan_Bean&gt;](http://dbpedia.org/resource/Alan_Bean) find another, matching examples.

Problem solution is described in the paper, but the main point is to rank entities based on the probability of being
relevant to either relation (text-based approach) or examples (structured/example-based approach).
Also combination of this approaches was proposed.

Tool execution looks like:
```sh
$ ebes-rank ./pp_data/ --shell
Loading triples from files in directory `./pp_data/`
Found 6 `.nq` files
-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
Starting interactive shell
h/help - print this help
l/load - load more triples from local files
q/query - make query
s/sample - make query from sample file
e/exit - exit shell
> sample
Sample file to use: pp_data/sample1.yml
Preparing ranking for sample file
Ranking 20 entities
...
------------------------------
Ranking - text-based:
 OO http://dbpedia.org/resource/Alan_Shepard - 2.149805060548479797831164338E-30
 xx http://dbpedia.org/resource/Louis_XVI_of_France - 1.930021450862217615174720805E-30
 xx http://dbpedia.org/resource/Odoacer - 1.923193744907281843843983081E-30
 OO http://dbpedia.org/resource/David_Scott - 1.874149873890035781955962027E-30
 OO http://dbpedia.org/resource/James_Irwin - 1.748944836057123244079001316E-30
 xx http://dbpedia.org/resource/Harry_Potter - 1.405266674597736522337448530E-30
...
~~~~~~~~~~
 precision -> 0.57143
------------------------------
Ranking - example-based:
 OO http://dbpedia.org/resource/Alan_Shepard - 0.01122268163024217365623154162
 OO http://dbpedia.org/resource/Edgar_Mitchell - 0.005020673360897814530419373892
 OO http://dbpedia.org/resource/James_Irwin - 0.004725339633786178381571175428
 OO http://dbpedia.org/resource/Charles_Duke - 0.004725339633786178381571175426
 OO http://dbpedia.org/resource/David_Scott - 0.003839338452451269935026580034
 xx http://dbpedia.org/resource/Brad_Pitt - 0.002658003544004725339633786178
...
~~~~~~~~~~
 precision -> 0.71429
```

## Running the tool

Use `setup.py` to install scripts `ebes-data` and `ebes-rank`. 

Or run with the Docker:
```sh
git clone https://github.com/GrosQuildu/example_based_entity_search
cd example_based_entity_search
docker build -t example_based_entity_search .
docker run -it -v `pwd`/pp_data:/home/user/data example_based_entity_search
```

Commands above will mount `./pp_data` directory in the container (as `data`) and spawn interactive shell.

At the beginning, dbpedia.org endpoint is loaded. Now lets hand-craft some query:
```sh
> query
Relation (R), as plain text: most powerful sith lords
Number of examples (integer): 2
Examples (X), as URIs.
   > http://dbpedia.org/resource/Palpatine
   > http://dbpedia.org/resource/Darth_Bane
Entities to rank, as URIs. Enter (blank line) to finish:
   > http://dbpedia.org/resource/Darth_Vader
   > http://dbpedia.org/resource/Darth_Maul
   > http://dbpedia.org/resource/Revan
   > http://dbpedia.org/resource/Sauron
   > http://dbpedia.org/resource/Yoda
   > http://dbpedia.org/resource/Qui-Gon_Jinn
   > http://dbpedia.org/resource/Mace_Windu
   > http://dbpedia.org/resource/Obi-Wan_Kenobi
   > http://dbpedia.org/resource/James_Bond
   > http://dbpedia.org/resource/G._K._Chesterton
   > 
Ranking 10 entities
 ~> ranking entity no 0 / 10
...
------------------------------
Ranking - text-based:
 http://dbpedia.org/resource/Darth_Vader - 1.405558168120405905088125607E-16
 http://dbpedia.org/resource/Revan - 1.398970640143771268550264186E-16
 http://dbpedia.org/resource/Darth_Maul - 1.324117820519982851698630489E-16
 http://dbpedia.org/resource/Mace_Windu - 8.523851958480738507552716070E-17
 http://dbpedia.org/resource/James_Bond - 4.851968887117295073021727182E-17
 http://dbpedia.org/resource/Obi-Wan_Kenobi - 4.633994123207575686367693457E-17
 http://dbpedia.org/resource/Qui-Gon_Jinn - 4.177985724050877073177547586E-17
 http://dbpedia.org/resource/Yoda - 3.461588235149503761620056721E-17
 http://dbpedia.org/resource/Sauron - 2.903879954877150388445926839E-17
 http://dbpedia.org/resource/G._K._Chesterton - 2.873440129133987334846882730E-17
------------------------------
Ranking - example-based:
 http://dbpedia.org/resource/Yoda - 0.007909604519774011299435028251
 http://dbpedia.org/resource/Qui-Gon_Jinn - 0.007909604519774011299435028249
 http://dbpedia.org/resource/Obi-Wan_Kenobi - 0.007909604519774011299435028249
 http://dbpedia.org/resource/Mace_Windu - 0.007909604519774011299435028249
 http://dbpedia.org/resource/Darth_Vader - 0.007909604519774011299435028249
 http://dbpedia.org/resource/Darth_Maul - 0.004519774011299435028248587571
 http://dbpedia.org/resource/Revan - 0.003389830508474576271186440679
 http://dbpedia.org/resource/Sauron - 0.001129943502824858757062146893
 http://dbpedia.org/resource/G._K._Chesterton - 0.001129943502824858757062146893
 http://dbpedia.org/resource/James_Bond - 0
```

It is pretty slow, because we need to do a lot of HTTP requests.
If you have a file with RDF triples you may use it instead. Run `load` command:
```sh
> load
Path to triples file or SPARQL endpoint url: data/sample5.nq
Loading triples from file `data/sample5.nq`
Switching PPGraph backend from remote endpoint to local files
```

Now, instead of writing query from nothing, execute ready query from a sample file:
```sh
> sample
Sample file to use: data/sample5.yml
Preparing ranking for sample file `data/sample5.yml`
Ranking 16 entities
 ~> ranking entity no 0 / 20
...
------------------------------
Ranking - text-based:
 OO http://dbpedia.org/resource/Boromir - 2.934713853186765002546771801E-23
 OO http://dbpedia.org/resource/Gandalf - 1.946241300960820230942345083E-23
 xx http://dbpedia.org/resource/Isildur - 1.878114332953757029860946284E-23
 OO http://dbpedia.org/resource/Gimli_(Middle-earth) - 6.883299615074009296265631534E-24
 xx http://dbpedia.org/resource/Saruman - 5.160899299947102073001672565E-24
 xx http://dbpedia.org/resource/King_Arthur - 4.060628871327632192167229192E-24
 xx http://dbpedia.org/resource/Sauron - 2.623427028120836409202092707E-24
 OO http://dbpedia.org/resource/Frodo_Baggins - 2.374169944796889318564718472E-24
 xx http://dbpedia.org/resource/Bilbo_Baggins - 2.214659323027436965422680638E-24
 OO http://dbpedia.org/resource/Legolas - 7.120837002688267337083381729E-25
 xx http://dbpedia.org/resource/Jason - 6.370315541440045388034964235E-25
 xx http://dbpedia.org/resource/Elrond - 6.082849141765376294898133877E-25
 xx http://dbpedia.org/resource/Manwë - 4.156643217958239018720883389E-25
 xx http://dbpedia.org/resource/Leir_of_Britain - 2.093834120300476037805863193E-25
 xx http://dbpedia.org/resource/Balin_(Middle-earth) - 1.321636116498028375912430476E-25
 xx http://dbpedia.org/resource/Peter_Pan - 7.969644887246789495404047439E-26
~~~~~~~~~~
 precision -> 0.60000
------------------------------
Ranking - example-based:
 OO http://dbpedia.org/resource/Frodo_Baggins - 0.01218521527213647441104792851
 xx http://dbpedia.org/resource/Saruman - 0.008935824532900081234768480911
 OO http://dbpedia.org/resource/Gandalf - 0.008935824532900081234768480911
 OO http://dbpedia.org/resource/Boromir - 0.008935824532900081234768480911
 OO http://dbpedia.org/resource/Gimli_(Middle-earth) - 0.007311129163281884646628757109
 xx http://dbpedia.org/resource/Sauron - 0.006498781478472786352558895208
 OO http://dbpedia.org/resource/Legolas - 0.006498781478472786352558895208
 xx http://dbpedia.org/resource/Bilbo_Baggins - 0.006498781478472786352558895208
 xx http://dbpedia.org/resource/Elrond - 0.004061738424045491470349309505
 xx http://dbpedia.org/resource/Isildur - 0.003249390739236393176279447604
 xx http://dbpedia.org/resource/Peter_Pan - 0.002437043054427294882209585703
 xx http://dbpedia.org/resource/Leir_of_Britain - 0.002437043054427294882209585703
 xx http://dbpedia.org/resource/King_Arthur - 0.002437043054427294882209585703
 xx http://dbpedia.org/resource/Jason - 0.002437043054427294882209585703
 xx http://dbpedia.org/resource/Balin_(Middle-earth) - 0.002437043054427294882209585703
 xx http://dbpedia.org/resource/Manwë - 0
~~~~~~~~~~
 precision -> 0.80000
```

If you don't have RDF file but want one, appropriate to a sample file, then use `ebes-data` (`dump_data.py`) script:
```sh
ebes-data -v pp_data/out.nq ./pp_data/sample1.yml not_relevant
# or
chmod a+w pp_data
docker run -it -v `pwd`/pp_data:/home/user/data example_based_entity_search \
       ebes-data -v data/out.nq ./data/sample1.yml relevant
```

To evaluate the tool on multiple triples files and samples, run `evaluate.py` script:
```sh
$ python ./example_based_entity_search/evaluate.py ./pp_data
Loading graphs...
...
Mean stats:
  Ranking with `text-based` method
    precision -> 0.25397
  Ranking with `examples-based` method
    precision -> 0.62937
```

## Data
#### Original
The base graph of structured data used in the paper was BTC-2009:

  * link: http://km.aifb.kit.edu/projects/btc-2009/
    
  * format: n-quads, plaintext file with triple+grap on every line, like:
    `<http://one.example/subject1> <http://one.example/predicate1 <http://one.example/object1> <http://example.org/graph3> .`
    
  * size: 17GiB, or 2.2GiB for testing

For queries (relations/topics and examples) three sets were used:

  * SemSearch'11
  
      * topics
          * link: http://km.aifb.kit.edu/ws/semsearch10/Files/samplequeries-list
          * full list (50 topics) is not available
      * examples
          * evaluation data (qrels) as URIs was used as examples, but is not available

  * INEX’07 and INEX’08
    
      * '07 and '08 not available, newer are though
      * link: https://inex.mmci.uni-saarland.de/data/documentcollection.html#lod
      * topics: a lot of them
      * examples
          * as qrels to wikipedia pages
          * semi-manuall mapping between pages and dbpedia URIs was done in the paper

#### Local

Topics and relevant data used in the paper are not accessible. I have manually forged some samples,
look for `.yml` files inside `pp_data` directory. As a base graph I used [dbpedia.org](https://dbpedia.org/sparql).
Triples relevant to samples can be found in `pp_data/*.nq` files. 

#### Structure of data for this tools 

To rank entities we need two things: triples graph (SemWeb data) and sample (query).

Triples graph can be parsed from a file in any format supported by rdflib
(RDF/XML, N3, NTriples, N-Quads, Turtle, TriX, RDFa and Microdata). Or remote SPARQL endpoint can be used.

Query should be stored in a [YAML](https://yaml.org/) file with the following format:

```yaml

---
topic: astronauts who walked on the Moon  # plain text relation
examples: 1  # use this number of top relevant entities as examples
relevant:  # examples and entities known to be relevant
    - http://dbpedia.org/resource/Neil_Armstrong
    - http://dbpedia.org/resource/Alan_Bean
not_relevant:  # entities known to be not relevant
    - http://dbpedia.org/resource/Samuel_Beckett
...
```

For "real" queries number of `relevant` entities would be equal to `examples` and `not_relevant`
entities would be a list of all examples we want to rank.

Note that the graph used should contain some triples related to every entity specified the query.
So either use remote endpoint (which is slow but trustworthy) or make sure that RDF file you use
contains necessary information. Possibly use `dump_data.py` (`ebes-data`) script for data acquisition. 

## Remarks
* General

    * I couldn't find a parser for data used in the paper (BTC-2009) efficient enough to be usable. 
    Both [rdflib](https://github.com/RDFLib/rdflib) (in python) and [Redland librdf](http://librdf.org/)
    (in C with python bindings) were tested. Because of that I used remote [dbpedia.org](https://dbpedia.org/sparql)
    endpoint as a data collection and have dumped relevant triples from it. 

    * The paper rank entities by computing "fitness" probability for every entity.
    But computing such probability for every known subject node seem impractical, as there are a lot of them.
    For example: dbpedia.org contains few millions entities, if processing one entity takes 0.1 sec,
    then processing one user query would take about a week. Don't know how this problem should be tackled nor
    how it was solved in the paper. I just assume that user provides all entities (probably both relevant and
    not-relevant) that should be ranked.
    
    * No way to return correct amount of matching examples. For example when query says `ten ancient Greek city`
    we can't handle this `ten`.   
    
* Text-based approach

  * Dirichlet smoothing part of equations was poorly described in the paper.
  It is uncertain how "Dirichlet smoothed model of the entire collection of triples" (probability P(t|theta_c))
  should be computed. Following standard approach (described in other resources) would require to iterate over
  all triples for every term in the relation, which is computationally expensive. Moreover, it would require
  every term to appear at least once in the collection, so as the probability won't be zero.
  Such requirement seems not to be stated in the paper. Also parameter `ni` was not provided.
  
  In the implementation I used a simplified version of Dirichlet model.
  Nominator part is set to 1 and `ni` parameter to number of known entities (amount of subjects in the graph).

  * Final probabilities are products of partial probabilities and therefore are small.
  This may lead to precision errors (somehow solved with python's `Decimal` module) and is not compatible with
  example-based approach (which produces much higher probabilities). This problem is not mentioned in the paper.

* Example-based approach

  * Representing an entity as a set of inlink/outlink triples doesn't make much sense for triples
   in which an object is Literal, because such triple won't match any other entity for sure.
   It is (intuitively) better to Nullify subjects in such triples.
   For example: 
      ```
      Entity A representation:
        A -> y -> v (A1), outlink
        A -> x -> B (A2), outlink

      Entity B representation:
        B -> y -> v (B1), outlink
        A -> x -> B (B2), inlink
      ```
    Only `A2-B2` matches. But if:
      ```
      Entity A representation:
        None -> y -> v (A1), outlink
        A -> x -> B (A2), outlink

      Entity B representation:
        None -> y -> v (B1), outlink
        A -> x -> B (B2), inlink
      ```
    Then both `A1-B2` and `A2-B2` match!
 