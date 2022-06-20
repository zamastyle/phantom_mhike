<hr><hr>
Switchboard is an app designed to make executing the approprite playbooks easier.
<br><br>
The process for this execution depends on two things:
<ul>
    <li>One active playbook that contains the switchboard <b>run playbooks</b> action</li>
    <li>Specifically named playbooks to match on</li>
</ul>
Executing the <b>run playbooks</b> accepts 3 inputs for playbook matching:
<ul>
    <li>Repository name - (Required) Indicates which repository to match playbooks from</li>
    <li>Product name - Accepts a string that represents the rule that generated the event</li>
    <li>Rule name - Accepts a comma seperated string of product names to match on</li>
</ul>
Types of named playbooks:
<ol>
    <li>Rule: &ltexact rule name to match&gt</li>
    <ul>
        <li>Matches if the literal rule name passed into <b>run playbooks</b> is the same</li>
    </ul>
    <li>Product: &ltexact product name to match&gt</li>
    <ul>
        <li>Matches if the playbook product name is a substring of the product name passed into <b>run playbooks</b></li>
    </ul>
    <li>Subject: &ltsubstring to partially match against the rule name text&gt</li>
    <ul>
        <li>Matches if the subject string is a substring of the rule name passed to <b>run playbooks</b></li>
    </ul>
    <li>Field: &ltexact field name to match&gt</li>
    <ul>
        <li>Matches if the playbook's specified field name is in the original artifact in the container</li>
    </ul>
</ol>
Once the set of matching playbooks is determined, those matching playbooks will be executed
<br><br>
The matching playbooks and total count of executed playbooks are outputs of the action
<br><br>
If no playbooks matched, no further playbooks will be executed by <b>run playbooks</b>
<hr><hr>
