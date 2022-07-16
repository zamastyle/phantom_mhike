## Intro
Anyone that has used playbooks in Splunk SOAR(Phantom) has used format blocks. 
They are core to managing several facets of playbook development. 

The default behavior of a format block is similar to a python string.format() call merging variables with static data. 
That is standard documented usage so this help is not going to dive into that. 
Instead we will be examining how to use %% in your format blocks to make a format block "loop". 
Loop is in quotes here because it is the closest way to describe what is happening here but it is not a conventional loop that you have any level of control over. 

The two use cases for the %% format strategy are input formatting to seperate multi-valued inputs into distinct action runs, and output formatting to make a 
message prettier and more human readable. 
Strictly speaking these are both more or less the same operation. they are only broken up in this help to make it easier to understand the intent.

## Output Format Loops
Output formatting is more similar to what people expect of a format block so let's begin with that.
For the purposes of our example we will be using artifacts but this applies to most sources that you can use as input. 

Imagine we have a container with the below artifacts in it:
```
label   deviceHostname   sourceAddress   sourceUserName
event   WOPR             1.1.1.1         David
event   The Gibson       2.2.2.2         Eugene
event   Quadra           3.3.3.3         Velociraptor
```
As you are probably familiar, if these values are used conventionally in a format block like this:
```
The device {0} with the address {1} owned by user {2} is doung bad stuff
```
The output is less than desireable, and is more likely to generate confusion than immediate action:
```
The device [WOPR,The Gibson,Quadra] with the address [1.1.1.1,2.2.2.2,3.3.3.3] owned by user [David,Eugene,Velociraptor] is doung bad stuff
```
This message is not very useful, but it can be cleaned up %% formatting.

If instead a format block like this is used:
```
%%
The device {0} at {1} owned by user {2} needs to be isolated
%%
```
The output becomes much more human friendly:
```
The device WOPR with the address 1.1.1.1 owned by user David is doung bad stuff
The device The Gibson with the address 2.2.2.2 owned by user Eugene is doung bad stuff
The device Quadra with the address 3.3.3.3 owned by user Velociraptor is doung bad stuff
```
In order for this type of format block to work properly, a few requirements need to be met:
- Each of the variables to substitute in must have the same number of values.
  - In this example each of the artifacts has the same fields so each variable is a list of three values.
  - If inputs with differing numbers of values in each variable are used, this will behave unpredictably.
- The `<format>:formatted_data` output of the format block must be used and *NOT* the `<format>:formatted_data.*` version. 
  - The `<format>:formatted_data.*` output tells the playbook to use the output as individual elements instead of one message. Here, the intent is to use a nicely formatted single message.

## Input Format Loops
The second type of use case for format loops is input format loops. These are very useful but are being used as inputs to actions rather than to format readable data

Using the same example artifacts we saw in the first example:
```
label   deviceHostname   sourceAddress   sourceUserName
event   WOPR             1.1.1.1         David
event   The Gibson       2.2.2.2         Eugene
event   Quadra           3.3.3.3         Velociraptor
```
If `artifacts:*.cef.sourceAddress` was passed as a standard input to an action in phantom, that input would produce a list of all 
`sourceAddress` values in the source artifacts in the container. The action would then execute once for each of the sourceAddresses. 
This is an intuitive behavior and individual action results are generated for each input as expected. 

_Unfortunately_, when working with code blocks (legacy custom functions) the behavior is entirly different. 
A list output in a code block variable that is passed to an action is not treated as a list but instead as a single object.

If a code block processed the artifacts above and created an output variable like this:
```
addresses = ["1.1.1.1","2.2.2.2","3.3.3.3"]
```
If that variable was then used as an input to an action like IP Reputation, instead of individual addresses, the action would attempt to process this single value:
```
"[\"1.1.1.1\",\"2.2.2.2\",\"3.3.3.3\"]".
```
This will never produce a useful result unless the action explicitly expects a string representation of a list (almost never). 

The problem can be fixed by using the input format block strategy. The format block content is extremely simple:
```
%%
{0}
%%
```
The code block output is used as the input for token `{0}`. With that setup, the `<format>:formatted_data.*` output of the format block can be passed to `IP Reputation`.

Because the `<format>:formatted_data.*` output was used for the action input, it will treat each value as an element and `IP Reputation` will run as intended.

The input format above is the simplest case. This can also be used for more complex formatting. For instance, formatting multiple splunk queries.
It is unlikely that a splunk query is going to execute properly as a single like this:
```
index=user_asset id="[\"David\",\"Eugene\",\"Velociraptor\"]"
```
But if an input format loop is used:
```
%%
index=user_asset id={0}
%%
```
Then 3 individual and usable splunk queries can be passed to a `RunQuery` action and get the job done.

The requirements for this type of format loop are very simple:
- Use the format blocks `<format>:formatted_data.*` output
 - For the input loop, individual elemnet are required as outputs so always use `<format>:formatted_data.*`
- If you are doing more complex formatting with multiple varibles, rememeber, each of the variables to substitute in must have the same number of values.
