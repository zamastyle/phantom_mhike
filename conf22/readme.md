<hr>
The files in this directory are in support of a conference talk given at Splunk .Conf 22

- "Building Smarter Playbooks Faster"
- SEC1216B
- Conference deck added here as a pdf

I deally there will be a link added here after the presentation to the recording

<hr>
<h><b>Global Util:</b></h><br>
The global util example provided here is an example of how to take repeatable boiler plate code and use a utility function as a module to store and import it<br>
The custom_prompt_example_with_reload file is an example playbook showing how to import and use the utility function

<br><b>Initial Setup:</b>
- Create a utility function in your repository with a clear name (ie. Global_Util) with no inputs or outputs
- Add the function definitions that you want to add. Make sure to include the <b>reload_module</b> function from the example
- Add another utility function with the name <b>__init__</b>

Once those steps are complete you are ready to import code into playbooks and utilities

<br><b>Things to know:</b>
- The global utility function is not usable as a normal utility. It was created to house function definitions to be imported elsewhere
- Use a seperate global utility function for each repository. Do not attempt to set python paths to allow cross repo talk
- Once the global utility function is saved, if you change the name of any function definitions, or add new functions, you need to reload the module. Failure to do so will result in your changes not being recognized
- It is <b>my best practice</b> to create a playbook that imports and executes the reload function
  - In dev, I run this playbook as needed
  - In prod, I schedule the playbook to run hourly to pick up changes on prod deploys
- If you add a manual reload call to your code in dev, do not leave it there when moving to prod. You do not want your module reloading every time it is used
- If you want to be able to import global util content into another utility function, make sure to import the global util module into the playbook that calls the utility
  - If you don't the global util won't be loaded and the utility function will fail to import it
  - Once you have imported it into the playbook, the module will be in memory and it will seem as if you do not need to import it into the calling playbook. DO NOT REMOVE IT FROM THE PLAYBOOK. If and when the module is unloaded from memory and the import isnt in the playbook, the utility attempting to import the code will start to fail again
  - ALWAYS import into the calling playbook before calling a utility that imports your global util playbook
- Whether you are importing into a playbook block or into a utility function, the import path is the same:
  - <code>import custom_functions.<your_utility_function_name></code>
- In my usage I have usually imported it as something easier to use:
  - <code>import custom_functions.Global_Util as utils</code>
- When reloading the module, if you have used my conventions and reload function, you simply call
  - <code>utils.reload_module(utils)</code>

<br><b>WARNINGS:</b>
- Beware of tricky memory. Just because something works after you un-did one of the things I mentioned above does not mean it will work after the module is unloaded from memory. I have chased this dragon. It is not a nice time. Don't be fooled by chached modules.
- Do <b>NOT</b> attempt to use python paths to allow cross repo sharing of global utilities. You will almost for sure have a bad time.
- This is soar hackery. Do not assume support is going to be happy about supporting this. You would be much better off reaching out to the community on #soar in the community slack before attampting to take issues regarding this to support.
