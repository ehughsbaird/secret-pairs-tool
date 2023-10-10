# Secret Pairs Tool

A python script to take a JSON file of the form:
```json
{
  "names": [
    "Name1",
    "Name2",
    "Name3"
  ],
  "twoway_force": [
    [ "Name1", "Name2" ]
  ],
  "twoway_block": [
    [ "Name1", "Name2" ],
    [ "Name1", "Name2" ]
  ],
  "force": {
    "Name1": "Name2"
  },
  "block": {
    "Name1": "Name2",
    "Name1": [ "Name2", "Name3" ]
  }
}
```

And produce a zip file for each name, containing a text file with the name of the person they have been assigned to.
This allows anonymous selection of pairs for events like secret santa without all being in the same physical place - simply modify the parameters file, and send everyone an email with the ZIP file named after them.

## Usage

There are two steps to using the tool.
The first is creating a parameters JSON file.
After that file is created, the script can be run to generate the pair assignments.

### Parameters File
Write or modify a parameters JSON file.
Below is an example file.

```json
{
  "names": [
    "Olivia",
    "Noah",
    "Emma",
    "Liam",
    "Amelia",
    "Oliver",
    "Sophia",
    "Elijah",
    "Ava",
    "Mateo",
    "Charlotte",
    "Lucas",
    "Isabella",
    "Levi",
    "Mia",
    "Leo",
    "Luna",
    "Ezra",
    "Evelyn"
  ],
  "twoway_force": [
    [ "Liam", "Emma" ]
  ],
  "twoway_block": [
    [ "Mia", "Mateo" ],
    [ "Ava", "Elijah" ]
  ],
  "force": {
    "Evelyn": "Ava"
  },
  "block": {
    "Leo": "Luna",
    "Liam": [ "Lucas", "Levi" ]
  }
}
```

#### `names`
This section lists the participants in the event.
Each participant will be assigned a pair, placed in a .txt file located within"THEIRNAME.zip".

#### `twoway_force`
This section forces particpants to be assigned to each other.
In this example, Liam must be assigned Emma, and Emma must be assigned Liam.

This can be left empty, as below.
```json
  "twoway_force": [ ]
```

#### `twoway_block`
This section excludes participants from being assigned each other.
In this example, Mia will not be assigned Mateo, and Mateo will not be assigned Mia.
Additionally, Ava will not be assigned Elijah, and Elijah will not be assigned Ava.

This can be left empty, as below.
```json
  "twoway_block": [ ]
```

#### `force`
This section will force the person on the right to be assigned to the person on the left.
In this example, Evelyn will always be assigned Ava.

This can be left empty, as below.
```json
  "force": { }
```

#### `block`
This section will prevent the person on the left from having any of the people on the right assigned to them.
In this example, Leo will never be assigned Luna, and Liam will never be assigned Lucas or Levi.

This can be left empty, as below.
```json
  "block": { }
```


### Run the script
Once the parameters JSON file is written, simply run the script.
```sh
python3 secret_pairs.py path/to/parameters_json_file.json
```
This will generate the zip files for each name in the current working directory.
More options can be seen by running the script with the `--help` argument.
