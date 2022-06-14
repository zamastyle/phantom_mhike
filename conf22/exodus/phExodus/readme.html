<h2>Requirements</h2>
<p>
Exodus migrates playbooks, custom functions, and assets via Phantom's rest API and uses containers under an <b>exodus</b> label to specify content that is being reviewed for migration. Several things are requires to effectively make this process flow work. You can run exodus from either your dev or your prod instance. The chosen host is where you will configure Exodus assets and "ingestion". Exodus does not technically ingest anything but the ingestion scheduling is used to define the interval time between checks for now content to be migrated<br>
<h3>API Tokens</h3>
You will need a Phantom API token for both your dev and your production environment<br>
Dev Permissions: Playbooks: R, Custom Code: RW, Apps: R, Assets: R<br>
Prod Permissions: Playbooks: R, Custom Code: RW, Apps: R, Assets: R<br>
Additional permissions for exodus ingestion host: Container: RW, Assets: W, Playbooks: W
<br><br>
<h3>Label</h3>
This app creates containers under the label <b>exodus</b>. This label should be created in your Phantom host that will run exodus. Permissions for this label should be restricted to roles that are authorized to review and approve content for production
<br><br>
<h3>Tag</h3>
Exodus identifies "new" content for migration based on 2 things: object ID and tags. Any playbook that has a new ID (because it has been changed) and a <b>prod</b> tag will be considered a candidate for migration. The <b>prod</b> tag should be created in your dev phantom environment for this purpose.
<br><br>
<h3>Playbook</h3>
Exodus identifies candidate playbooks and custom functions and creates <b>exodus</b> containers. Once these containers are created, the only requirement left to signal Exodus to move the content to prod is to run the Exodus action <b>add approval</b>. The methodology for how that action is invoked and what the process looks like is defined by the organization. It can be as simple as requiring leads on the dev team to review all new exodus containers and manually run the add approval action if they approve or close the container if they don't approve. It is recommended that an active playbook be created for the exodus containers that builds and sends an approval request via prompts, slack, email, etc in order to make your process smoother and more auditable. It would be wise to store these playbooks in an "admin" repo to prevent unauthorized users from adversly modifying the approval process playbook.
<br><br>
