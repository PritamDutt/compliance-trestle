# Trestle Specifications (v0.0.1)

## Table of Contents

- [Purpose](<#purpose>)
- [Users](<#users>)
- [Scope](<#scope>)
- [Trestle commands](<#trestle-commands>)
  - [Draft commands](<#draft-commands>)
- [Future work](<#future-work>)
  - [Deploy commands](<#deploy-commands>)
  - [Monitor commands](<#monitor-commands>)
  - [Reporting commands](<#reporting-commands>)

## Purpose

This document contains detail specifications of the Trestle commands.

Trestle offers various commands to simplify operations at different steps in compliance management and reporting.

Trestle assumes all security and compliance specifications and requirements are expressed in OSCAL format.

## Users

Trestle aims at compliance engineers who are familiar with various software development tools such as Git, CI/CD and command line tools.

Users of Trestle are also expected to be comfortable with editing OSCAL files in YAML/JSON/XML format.

## Scope

The scope of this document is to describe the purpose and expected behaviour of various trestle commands for manipulating OSCAL documents ONLY. This will not be all of trestle. Workflow commands will be subsequent / expanded on this.

## Trestle Commands

### Draft Commands

For the draft phase of compliance engineering, trestle provides the following commands to facilitate various draft related operations.

#### `trestle init`

This command will create a trestle project in the current directory with necessary directory structure and trestle artefacts. For example, if we run `trestle init` in a directory, it will create a directory structure like below for different artefacts:

~~~
.
├── .trestle
├── dist
│   ├── catalogs
│   ├── profiles
│   ├── target-definitions
│   ├── system-security-plans
│   ├── assessment-plans
│   ├── assessment-results
│   └── plan-of-action-and-milestones
├── catalogs
├── profiles
├── target-definitions
├── component-definitions
├── system-security-plans
├── assessment-plans
├── assessment-results
└── plan-of-action-and-milestones
~~~

`.trestle` directory is a special directory containing various trestle artefacts to help run various other commands.

`dist` directory will contain the merged or assembled version of the models located on the source model directories (at the project root level) which are: `catalogs`, `profiles`, `target-definitions`, `component-definitions`, `system-security-plans`, `assessment-plans`, `assessment-results` and `plan-of-action-and-milestones`.

Notice that trestle is a highly opinionated tool and, therefore, the names of the files and directories that are created by any of the `trestle` commands and subcommands MUST NOT be changed manually.

#### `trestle create`

This command will create an initial directory structure for various OSCAL models including sample JSON files and subdirectories representing parts of the model. For example, `trestle create catalog -o catalog-cat1` will create a directory structure of a sample catalog like below.

~~~
.
├── .trestle
├── dist 
│   └── catalogs
│       └── catalog-cat1.json
└── catalogs
    └── catalog-cat1
        ├── catalog.json
        └── groups
            ├── 00000__group
            │   ├── group.json
            │   └── controls
            │       ├── 00000__control.json
            │       └── 00001__control.json
            └── 00001__group
                ├── group.json
                └── controls
                    ├── 00000__control.json
                    ├── 00001__control.json
                    └── 00002__control.json
...
~~~

The following subcommands are currently supported:

- `trestle create catalog`: creates a directory structure of a sample OSCAL catalog model under the `catalogs` folder. This folder can contain multiple catalogs.
- `trestle create profile`: creates a directory structure of a sample OSCAL profile model under the `profiles` folder. This folder can contain multiple profiles.
- `trestle create target-definition`: creates a directory structure of a sample target-definition model under the `target-definitions` folder. This folder can contain multiple target-definitions.
- `trestle create component-definition`: creates a directory structure of a sample component-definition model under the `component-definitions` folder. This folder can contain multiple component-definitions.
- `trestle create system-security-plan`: creates a directory structure of a sample system-security-plan model under the `system-security-plans` folder. This folder can contain multiple system-security-plans.
- `trestle create assessment-plan`: creates a directory structure of a sample assessment-plan under the `assessment-plans` folder. This folder can contain multiple assessment-plans.
- `trestle create assessment-result`: creates a directory structure of a sample assessment-result under the `assessment-results` folder. This folder can contain multiple assessment-results.
- `trestle create plan-of-action-and-milestone`: creates a directory structure of a sample plan-of-action-and-milestone under the `plan-of-action-and-milestones` folder. This folder can contain multiple plan-of-action-and-milestones.

The following options are supported:

- `-o or --output`: specifies the name/alias of a model. It is used as the prefix for the output filename under the `dist` directory and for naming the source subdirectories under  `catalogs`, `profiles`, `target-definitions`, `component-definitions`, `system-security-plans`, `assessment-plans`, `assessment-results` or `plan-of-action-and-milestones`.

The user can edit the parts of the generated OSCAL model by modifying the sample content in those directories.

The initial level of decomposition of each type of model varies according to the model type.
This default or reference decomposition behaviour can be changed by modifying the rules in a `.trestle/config file`. These rules can be written as a sequence of `trestle split` commands.

#### *Catalog default decomposition*

For `catalog`, the inital sample content is broken down as shown below:

~~~
.
├── .trestle
├── dist 
│   └── catalogs
│       └── catalog-cat1.json
└── catalogs
    └── catalog-cat1
        ├── catalog.json
        └── groups
            ├── groups.json        
            ├── 00000__group            
            │   ├── group.json
            │   └── controls
            │       ├── 00000__control.json
            │       └── 00001__control.json
            └── 00001__group
                ├── group.json
                └── controls
                    ├── 00000__control.json
                    └── 00001__control.json
...
~~~

- a `catalog.json` file containing a catalog JSON object without the `catalog.groups` property.
- `catalog.groups` property is broken down into a subdirectory called `groups`. The `groups` subdirectory has a `groups.json` file containing a JSON object named `groups` as an empty array.
- For each group in the `catalog.groups` array list, an indexed subdirectory is created containing a `group.json` with a group object as its contents without the `controls` property.
- `catalog.groups[i].controls` property in each group is broken down into subdirectories called `controls`. The `controls` subdirectory has a `controls.json` file containing a JSON object named `controls` as an empty array.
- For each control in a `catalog.groups[i].controls` array list, an indexed JSON file is created representing the contents of a control.

#### *Profile default decomposition*

For `profile`, the initial sample content is not broken down by default as shown below.

~~~
.
├── .trestle
├── dist
│   └── profiles
│       └── profile-myprofile.json
└── profiles
    └── profile-myprofile
        └── profile.json
...
~~~

- `profile.json` file has the content of the OSCAL profile.

#### *Target-definition default decomposition*

For `target-definition`, the initial sample content is broken down as shown below:

~~~
.
├── .trestle
├── dist
│   └── target-definitions
│       └── target-definition-mytargets.json
└── target-definitions
    └── target-definition-mytargets
        ├── target-definition.json
        └── targets
            ├── targets.json
            ├── 74ccb93f-07d1-422a-a43d-3c97bae4c514__target
            │   ├── target.json
            │   └── target-control-implementations
            │       ├── target-control-implementations.json
            │       ├── 00000__target-control-implementation.json
            │       └── 00001__target-control-implementation.json
            └── 953a2878-2a21-4a0f-a9fa-3a37b61b9df8__target
                ├── target.json
                └── target-control-implementations
                    ├── target-control-implementations.json
                    ├── 00000__target-control-implementation.json
                    └── 00001__target-control-implementation.json
...
~~~

- a `target-definition.json` file containing a target definition JSON object except for the `target-definition.targets` property.
- `target-definition.targets` property is broken down into a subdirectory named `targets`. The `targets` subdirectory has a `targets.json` file containing a JSON object named `targets` as an empty object.
- For each component in the `target-definition.targets` uniquely identified by a property labelled with the target's uuid, a subdirectory named after the `{{uuid}}__target` is created containing a `target.json` file. This file contains a target JSON object without the `target-control-implementations` property.
- `target-definition.components.{{uuid}}.target-control-implementations` property is broken down into subdirectories called `target-control-implementations`. The `target-control-implementations` subdirectory has a `target-control-implementations.json` file containing a JSON object named `target-control-implementations` as an empty object.
- For each target control implementation in a `target-definition.components.{{uuid}}.target-control-implementations` array list, an indexed JSON file is created representing the contents of a target control implementation.

At the moment, the initial sample content for the other model types (`component-definition`, `system-security-plan`, `assessment-plan`, `assessment-result` and `plan-of-action-and-milestone`) is TBD.

The user can increase the level of decomposition by using `trestle split` command.

#### `trestle import`

This command allows users to import existing OSCAL files so that they can be managed using trestle. For example `trestle import -f existing_catalog.json -o my_existing_catalog` will import `existing_catalog.json` into a new folder under `catalogs` as shown below:

~~~
.
├── .trestle
├── dist 
│   └── catalogs
│       ├── my_existing_catalog.json 
│       └── catalog-cat1.json 
└── catalogs
    ├── my_existing_catalog
    │   ├── catalog.json
    │   └── groups
    │       ├── groups.json
    │       └── 00000__group
    │           ├── group.json
    │           └── controls
    │               ├── controls.json    
    │               ├── 00000__control.json
    │               └── 00001__control.json
    └── catalog-cat1
        ├── catalog.json
        └── groups
            ├── groups.json
            ├── 00000__group
            │   ├── group.json
            │   └── controls
            │       ├── controls.json                
            │       ├── 00000__control.json
            │       └── 00001__control.json
            └── 00001__group
                ├── group.json
                └── controls
                    ├── controls.json                    
                    ├── 00000__control.json
                    └── 00001__control.json
...
~~~

The following options are supported:

- `-f or --file`: specifies the path of an existing OSCAL file.
- `-o or --output`: specifies the name/alias of a model. It is used as the prefix for the output filename under the `dist` directory and for naming the source subdirectories under  `catalogs`, `profiles`, `target-definitions`, `component-definitions`, `system-security-plans`, `assessment-plans`, `assessment-results` or `plan-of-action-and-milestones`.

The import subcommand can determine the type of the model that is to be imported by the contents of the file.

Note that the import command will decompose the file according to the default decomposing rules already mentioned in the `trestle create` section. Similarly to `trestle create`, the user can increase the level of decomposition by using `trestle split` command.

#### `trestle replicate`

This command allows users to replicate a certain OSCAL model (file and directory structure). For example `trestle replicate catalog -i cat1 -o cat11` will replicate the Catalog cat1 into `cat11` directory. It can also regenerate all the UUIDs as required.

#### `trestle split`

This command allows users to further decompose a trestle model into additional subcomponents.

The following options are currently supported:

- `-f or --file`: this option specifies the file path of the json/yaml file containing the elements that will be split.
- `-e or --elements`: specifies the model subcomponent element(s) (JSON/YAML property path) that is/are going to be split. Multiple elements can be specified at once using a comma-separated value. If the element is of JSON/YAML type array list and you want trestle to create a separate subcomponent file per array item, the element needs to be suffixed with `.*`. If the suffix is not specified, split will place all array items in only one separate subcomponent file. If the element is a collection of JSON Schema additionalProperties and you want trestle to create a separate subcomponent file per additionalProperties item, the element also needs to be suffixed with `.*`. Similarly, not adding the suffix will place all additionalProperties items in only one separate subcomponent file.

In the near future, `trestle split` should be smart enough to figure out which json/yaml files contain the elemenets you want to split. In that case, the `-f` option would be deprecated and only the `-e` option will be required. In order to determine which elements the user can split at the level the command is being executed, the following command can be used:
`trestle split -l` which would be the same as `trestle split --list-available-elements`

#### Example

To illustrate how this command could be used consider a catalog model named `mycatalog` that was created via `trestle create catalog -o mycatalog` or imported via `trestle import -f mycatalog.json`.

~~~
.
├── .trestle
├── dist 
│   └── catalogs
│       └── mycatalog.json 
└── catalogs
    └── mycatalog
        ├── catalog.json
        └── groups
            ├── groups.json
            ├── 00000__group
            │   ├── group.json
            │   └── controls
            │       ├── controls.json
            │       ├── 00000__control.json
            │       └── 00001__control.json
            └── 00001__group
                ├── group.json
                └── controls
                    ├── controls.json
                    ├── 00000__control.json
                    └── 00001__control.json
...
~~~

**Step 1**: A user might want to decompose the `metadata` property from `catalog.json`. In order to achieve that he/she would run from `$BASE_FOLDER/catalogs/mycatalog` the command `trestle split -f catalog.json -e 'catalog.metadata'`. This would create a `metadata.json` file at the same level as `catalog.json` and move the whole `metadata` property/section from `catalog.json` to `metadata.json` as below:

~~~
.
├── .trestle
├── dist 
│   └── catalogs
│       └── mycatalog.json 
└── catalogs
    └── mycatalog
        ├── catalog.json      #removed metadata property from this file
        ├── metadata.json     #contains the metadata JSON object
        └── groups
            ├── groups.json        
            ├── 00000__group
            │   ├── group.json
            │   └── controls
            │       ├── controls.json            
            │       ├── 00000__control.json
            │       └── 00001__control.json
            └── 00001__group
                ├── group.json
                └── controls
                    ├── controls.json                
                    ├── 00000__control.json
                    └── 00001__control.json
...
~~~

The future version of this command would be: `trestle split -e 'metadata'`
Notice that in that case, the root property `catalog.` was ommitted and infered by trestle based on the directory the command was executed from.

**Step 2**: Suppose now the user wants to further break down the `revision-history` property under the `metadata` subcomponent. The command to achieve that would be `trestle split -f metadata.json -e 'metadata.revision-history'` which would result in the replacement of the `metadata.json` file by a `metadata` directory containing a `metadata.json` file and a `revision-history.json` file as shown below:

~~~
.
├── .trestle
├── dist 
│   └── catalogs
│       └── mycatalog.json 
└── catalogs
    └── mycatalog
        ├── catalog.json
        ├── metadata
        │   ├── metadata.json  #metadata JSON value without revision-history property
        │   └── revision-history.json
        └── groups
            ├── groups.json          
            ├── 00000__group
            │   ├── group.json
            │   └── controls
            │       ├── controls.json            
            │       ├── 00000__control.json
            │       └── 00001__control.json
            └── 00001__group
                ├── group.json
                └── controls
                    ├── controls.json                      
                    ├── 00000__control.json
                    └── 00001__control.json
...
~~~

The future version of this command would be:

- `trestle split -e 'metadata.revision-history'` when executed from `$BASE_FOLDER/catalogs/mycatalog`

**Step 3**: Knowing that `revision-history` is an array list, suppose the user wants to edit each item in that array list as a separate subcomponent or file. That can be achieved by running: `trestle split -f metadata/revision-history.json -e 'revision-history.*'` (notice the `.*` referring to each element in the array) which would replace the `revision-history.json` file by a `revision-history` directory containing multiple files prefixed with a 5 digit number representing the index of the array element followed by two underscores and the string `revision-history.json` as shown below:

~~~
.
├── .trestle
├── dist 
│   └── catalogs
│       └── mycatalog.json 
└── catalogs
    └── mycatalog
        ├── catalog.json
        ├── metadata
        │   ├── metadata.json
        │   └── revision-history
        │       ├── revision-history.json        
        │       ├── 00000__revision-history.json
        │       ├── 00001__revision-history.json
        │       └── 00002__revision-history.json                
        └── groups
            ├── groups.json
            ├── 00000__group
            │   ├── group.json
            │   └── controls
            │       ├── controls.json            
            │       ├── 00000__control.json
            │       └── 00001__control.json
            └── 00001__group
                ├── group.json
                └── controls
                    ├── controls.json                    
                    ├── 00000__control.json
                    └── 00001__control.json
...
~~~

The future version of this command would be:

- `trestle split -e 'metadata.revision-history.*'` when executed from `$BASE_FOLDER/catalogs/mycatalog`, or;
- `trestle split -e 'revision-history.*'` when executed from `$BASE_FOLDER/catalogs/mycatalog/metadata`

OSCAL also makes use of `additionalProperties` supported by JSON Schema which behaves as a map or dict. OSCAL normally uses this feature as a way to assign multiple objects to a property without necessarily having to enforce a specific order as is the case with JSON array properties. It is like assigning a map/dict to a property. An example of such property in the catalog schema is the `responsible-parties` under `metadata`. One example of contents for a `responsible-parties` property is:

~~~
"responsible-parties": {
  "creator": {
    "party-uuids": [
      "4ae7292e-6d8e-4735-86ea-11047c575e87"
    ]
  },
  "contact": {
    "party-uuids": [
      "4ae7292e-6d8e-4735-86ea-11047c575e87"
    ]
  }
}
~~~

A more evident example of this type of property is in the `components` property under the `target-definition` schema.

**Step 4**: Suppose the user wants to split the `responsible-parties` property in order to be able to edit each arbitrary key/value object under it as a separate file. The command to achieve that would be `trestle split -f metadata/metadata.json -e metadata.responsible-parties.*` (notice the `.*` at the end referring to each key/value pair in the map) which would result in creating a directory called `responsible-parties` and multiple JSON files under it, one for each `additionalProperty` using the key of the `additional property` as the name of the JSON file. The result is shown below:

~~~
.
├── .trestle
├── dist 
│   └── catalogs
│       └── mycatalog.json 
└── catalogs
    └── mycatalog
        ├── catalog.json
        ├── metadata
        │   ├── metadata.json
        │   ├── revision-history
        │   │   ├── revision-history.json        
        │   │   ├── 00000__revision-history.json
        │   │   ├── 00001__revision-history.json
        │   │   └── 00002__revision-history.json       
        │   └── responsible-parties
        │       ├── responsible-parties.json        
        │       ├── creator__responsible-party.json
        │       └── contact__responsible-party.json       
        └── groups
            ├── groups.json        
            ├── 00000__group
            │   ├── group.json
            │   └── controls
            │       ├── controls.json
            │       ├── 00000__control.json
            │       └── 00001__control.json
            └── 00001__group
                ├── group.json
                └── controls
                    ├── controls.json                
                    ├── 00000__control.json
                    └── 00001__control.json
...
~~~

The future version of this command would be:

- `trestle split -e 'metadata.responsible-parties.*'` when executed from `$BASE_FOLDER/catalogs/mycatalog`, or;
- `trestle split -e 'responsible-parties.*'` when executed from `$BASE_FOLDER/catalogs/mycatalog/metadata`

An example of a sequence of trestle split and merge commands and the corresponding states of the files/directories structures can be found in `test/data/split_merge` folder in this repo.

#### `trestle merge`

The trestle merge command is the reversal of `trestle split`. This command allows users to reverse the decomposition of a trestle model by aggregating subcomponents scattered across multiple files or directories into the parent JSON/YAML file of a specific directory.

The following options are currently supported:

- `-f or --file`: this option specifies the file/directory paths of the files and/or directories containing the elements that will be merged.
- `-d or --destination`: specifies the parent JSON/YAML file in which all the properties from the files/directories passed in via the `-f` option will be merge into. Notice that the properties to be merged will be placed into the root property of the destination file as opposed to be placed at the same level as the root property.

In other words, a command such as `trestle merge -f uuid.json,metadata.json,groups.json,back-matter.json -d catalog.json` would merge the properties inside each of the files passed in via the `-f` option to the destination file specified with the `-d` option.

In the near future, trestle merge should be smart enough to figure out which json files contain the elemenets that you want to be merged as well as the destination file that the elements should be placed into (every directory contains just one possible destination/parent file). In that case, both `-f` option and `-d` would be deprecated and the commands would look like: `trestle merge -e uuid,metadata,groups,back-matter`
The only required option would be:

- `-e or --elements`: specifies the properties (JSON/YAML path) that will be merged. In the command `trestle merge -e uuid,metadata,groups,back-matter`, the properties `uuid` from `uuid.json`, `metadata` from `metadata.json`, `groups` property from `groups.json` or `groups` directory, and `back-matter` property from `back-matter.json` would all be moved/merged into `catalog.json`.
  In order to determine which elements the user can merge at the level the command is being executed, the following command can be used:
  `trestle merge -l` which would be the same as `trestle merge --list-available-elements`

#### `trestle assemble`

This command assembles all contents (files and directories) representing a specific model into a single OSCAL file located under `dist` folder. For example, `trestle assemble catalog -i mycatalog` will traverse the `catalogs/mycatalog` directory and its children and combine all data into a OSCAL file that will be written to `dist/catalogs/mycatalog.json`. Note that the parts of catalog `mycatalog` can be written in either YAML/JSON/XML (e.g. based on the file extension), however, the output will be generated as YAML/JSON/XML as desired. Trestle will infer the content type from the file extension and create the model representation appropriately in memory and then output in the desired format. Trestle assemble will also validate content as it assembles the files and make sure the contents are syntactically correct.

#### `trestle add`

This command allows users to add an OSCAL model to a subcomponent in source directory structure of the model. For example, `trestle add -f ./catalog.json -e metadata.roles ` will add the following property under the `metadata` property for a catalog that will be written to the appropriate file under `catalogs/mycatalog` directory:

~~~
"roles": [
  {
    "id": "REPLACE_ME",
    "title": "REPLACE_ME"
  }
~~~

Default values for mandatory datatypes will be like below. All UUID's will be populated by default whether or not they are mandatory.

~~~
- DateTime: <Current date-time>
- Boolean: False
- Integer: 0 
- String: REPLACE_ME
- Float/Double: 0.00
- Id field: Auto generated UUID
~~~

#### `trestle remove`

The trestle remove command is the reversal of `trestle add`.

#### `trestle validate`

This command will validate the content of the specified file by combining all its children. For example, `trestle validate -f cat1yaml` will create the cat1 catalog in the model and make sure it is is a valid Catalog. By default this command do a "shallow validation" where it just checks for syntax error and makes sure the model can be generated from the file content. For extensive validation, `trestle validate` supports "deep validation" like cross-linking ids when additional parameters(e.g. `--mode deep-validation`) are passed. We envision that users will run this command occassionally to make sure the contents are valid.

## Future work

#### `trestle generate`

This command will allow generating default values such as UUID

### Deploy Commands

For the deploy phase of compliance engineering, trestle provides the following commands to facilitate various operations.

- `trestle plan`: Fetch current deployed controls and check what needes to be updated. This is like `terraform plan`.

- `trestle apply`: Apply the diffs or output of the `trestle plan` command in order to deploy the controls or other desired state. This is like `terraform apply`.

- `trestle ci init`: Initialize CI/CD pipeline for this project. It may create artefacts in `.trestle` directory.

- `trestle ci run`: Run the CI/CD pipeline. If a pipeline name is not provided, it will run all piplelines for this project.

- `trestle ci stop`: Stop the CI/CD pipleline. If a pipeline name is not provided, it will run all piplelines for this project.

### Monitoring Commands

Trestle provides the following commands to facilitate various monitoring operations.

*TBD*

- `trestle fetch`: This command will fetch facts about a control

### Reporting Commands

Trestle provides the following commands to facilitate various reporting operations.