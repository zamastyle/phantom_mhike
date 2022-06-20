<hr>
The files in this directory are in support of a conference talk given at Splunk .Conf 22

- "Building Smarter Playbooks Faster"
- SEC1216B
- Conference deck added here as a pdf

I deally there will be a link added here after the presentation to the recording

<hr>
<h2>Global Util:</h2>
<i>During conf I was asked why, with other options available for managing custom code content, I support this concept of hijacking a utility function as an imported module. The reasoning is fairly simple. This process is easy to implement, easy to understand, and is as close to "native" as you can get in the platform. Anyone who is familiar with what is happening knows how to utilize, locate, and update the module without having to leave the platform UI. Keep it simple.</i><br><br>

The global util example provided here is an example of how to take repeatable boiler plate code and use a utility function as a module to store and import it<br>
The custom_prompt_example_with_reload file is an example playbook showing how to import and use the utility function

<h2>Initial Setup:</h2>
<ul>
<li>Create a utility function in your repository with a clear name (ie. Global_Util) with no inputs or outputs
<li>Add the function definitions that you want to add. Make sure to include the <b>reload_module</b> function from the example
<li>Add another utility function with the name <b>__init__</b>
</ul>
Once those steps are complete you are ready to import code into playbooks and utilities

<h2>Things to know:</h2>
<ul>
<li>The global utility function is not usable as a normal utility. It was created to house function definitions to be imported elsewhere
<li>As shown in the example, your function definitions should be outside of the utility function definition. If you store them within the utility function definition, they will not be accessible to import
<li>Use a seperate global utility function for each repository. Do not attempt to set python paths to allow cross repo talk
<li>Once the global utility function is saved, if you change the name of any function definitions, or add new functions, you need to reload the module. Failure to do so will result in your changes not being recognized
<li>It is <b>my best practice</b> to create a playbook that imports and executes the reload function
<ul>
  <li>In dev, I run this playbook as needed
  <li>In prod, I schedule the playbook to run hourly to pick up changes on prod deploys
</ul>
<li>If you add a manual reload call to your code in dev, do not leave it there when moving to prod. You do not want your module reloading every time it is used
<li>If you want to be able to import global util content into another utility function, make sure to import the global util module into the playbook that calls the utility
<ul>
  <li>If you don't the global util won't be loaded and the utility function will fail to import it
  <li>Once you have imported it into the playbook, the module will be in memory and it will seem as if you do not need to import it into the calling playbook. DO NOT REMOVE IT FROM THE PLAYBOOK. If and when the module is unloaded from memory and the import isnt in the playbook, the utility attempting to import the code will start to fail again
</ul>
<ul><li>ALWAYS import into the calling playbook before calling a utility that imports your global util playbook</ul>
<li>Whether you are importing into a playbook block or into a utility function, the import path is the same:
<ul><li><code>import custom_functions.<your_utility_function_name></code></ul>
<li>In my usage I have usually imported it as something easier to use:
<ul><li><code>import custom_functions.Global_Util as utils</code></ul>
<li>When reloading the module, if you have used my conventions and reload function, you simply call
<ul><li><code>utils.reload_module(utils)</code></ul>
</ul>

<br><h2>WARNINGS:</h2>
 <ul>
<li>Beware of tricky memory. Just because something works after you un-did one of the things I mentioned above does not mean it will work after the module is unloaded from memory. I have chased this dragon. It is not a nice time. Don't be fooled by chached modules.
<li>Do <b>NOT</b> attempt to use python paths to allow cross repo sharing of global utilities. You will almost for sure have a bad time.
<li>This is soar hackery. Do not assume support is going to be happy about supporting this. You would be much better off reaching out to the community on #soar in the community slack before attampting to take issues regarding this to support.
</ul>
