 This is a general reference to the urls, filters, and operators available via rest https calls in Phantom. This is not exhaustive and you do have to be authenticated to use these. More often than not, you can get the data you need from the phantom UI, but in scripts and custom playbook utilities, this API is probably where you will end up going. It is almost always faster and easier to script up a report than to try to harvest the report data from the UI directly. 



#  Rest endpoints of note
/rest/container<br/>
/rest/container/\<id\><br/>
/rest/container/\<id\>/comments<br/>
/rest/container/\<id\>/attachments<br/>
/rest/container/\<id\>/playbook_runs<br/>
/rest/container/\<id\>/actions

/rest/workbook_task<br/>
/rest/workbook_phase

/rest/app

/rest/app_run<br/><br/>
/rest/app_run/\<id\><br/>
/rest/app_run/\<id\>/log<br/>

/rest/artifact<br/>
/rest/artifact/\<id\>

/rest/playbook<br/>
/rest/playbook/\<id\>

/rest/playbook_run<br/>
/rest/playbook_run/\<id\><br/>
/rest/playbook_run/\<id\>/log

/rest/action_run<br/>
/rest/action_run/\<id\><br/>
/rest/action_run/\<id\>/app_runs?include_expensive

/rest/container_attachment<br/>
/rest/container_attachment/\<id\>

/rest/container_comment<br/>
/rest/container_comment/\<id\>

/rest/decided_list<br/>
/rest/decided_list/<list_name>

/rest/scm

/rest/ingestion_status

/rest/app_status

/rest/health

/rest/notification_summary

/rest/system_settings

/rest/container_options<br/>
/rest/container_status<br/>
/rest/severity<br/>



#  Special Formatting

If needed, list are unique data sets and can be formatted in CSV:

  <code>/rest/decided_list/<list_name>/formatted_content?_output_format=csv</code>

------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Pretty Names
For objects that contain IDs of other objects, you can frequently get the pretty name of the ID to return in the object by adding <br/>
  <code>?pretty</code><br/>
You cannot filter or otherwise interact with the pretty values via url parameters

------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Expensive Fields
In some cases you can get more detail from a record by using <br/>
  <code>?include_expensive</code><br/>
but its not frequently useful and it is named expensive because it is.<br/>
This can substantially slow down some query operations

 
 
# Searching CEF Values
 
the /rest/artifact endpoint has a unique search ability that can come in handy. In most cases you want to create a very specific rest query but sometimes you just have to search everything. It is recommended that you include a date filter as well as any other applicable filters to speed up the response and reduce the overhead on the search.

Basic search syntax (searching for the term cve-0000 in all cef fields across all artifacts)<br/>
<code>/rest/artifact?search_cef=["cve-0000"]</code>

Filtered search for the same term (after Reb 10th and with a severity of high)<br/>

<code>/rest/artifact?_filter_create_time__gt="2023-02-10T00:00:00.000000Z"&_filter_severity="high"&search_cef=["cve-0000"]</code>
 

#  Filtering Data

----------------------------------------
Include
----------------------------------------
To include specific data use _filter

Example:<br/>
<code>?_filter_name="test"</code><br/>
• Shows only results that exactly match "test" in the name field

----------------------------------------
Exclude
----------------------------------------
To exclude specific data use _exclude

Example:<br/>
<code>?_exclude_name="test"</code><br/>
• Shows only results that do not exactly match "test" in the name field

----------------------------------------
Sub-fields
----------------------------------------
To access subfields in data use __ between parent and child fields

Example:<br/>
<code>?_exclude_cef__username__startswith="john"</code><br/>
• username in this case is a key in the cef dictionary and must be accessed via its parent key

----------------------------------------
Sort
----------------------------------------
To sort on a field use<br/>
<code>?sort=<filed_name></code>

----------------------------------------
Order
----------------------------------------
To specify asceding or descending order for your sort use<br/>
<code>?order=asc</code><br/>
or<br/>
<code>?order=desc</code><br/>

----------------------------------------
Max Results or Page Size
----------------------------------------
Default max results returned is 10. To get more or less use<br/>
<code>?page_size=<int></code>

To paginate and parse through pages, use<br/>
<code>?page=<int></code>

The total number of pages is included in the json response as num_pages<br/>
To get all results in a single page use<br/>
<code>?page_size=0</code>



#  Filter Operators

For all of the below operators, _filter and _exclude are interchageable as needed

----------------------------------------
__isnull
----------------------------------------
Matches null values or not null values based on boolean parameter<br/>
Example:<br/>
<code>?_filter_name__isnull=True</code><br/>
• True shows null matches<br/>
• False shows not null matches

----------------------------------------
__gt
----------------------------------------
Matches values greater than integer or date parameter<br/>
Example:<br/>
<code>?_filter_artifact_count__gt=0</code><br/>
<code>?_filter_create_time__gt="2018-01-01T00:00:00.000000Z"</code>

----------------------------------------
__gte
----------------------------------------
Matches values greater than or equal to integer or date parameter<br/>
Example:<br/>
<code>?_filter_artifact_count__gte=1</code><br/>
<code>?_filter_create_time__gte="2018-01-01T00:00:00.000000Z"</code>

----------------------------------------
__lt
----------------------------------------
Matches values less than integer or date parameter<br/>
Example:<br/>
<code>?_filter_artifact_count__lt=10</code><br/>
<code>?_filter_create_time__lt="2018-01-01T00:00:00.000000Z"</code>

----------------------------------------
__lte
----------------------------------------
Matches values less than or equal to integer or date parameter<br/>
Example:<br/>
<code>?_filter_artifact_count__lte=150</code><br/>
<code>?_filter_create_time__lte="2018-01-01T00:00:00.000000Z"</code>

----------------------------------------
__startswith
----------------------------------------
Matches values that start with the string parameter<br/>
Example:<br/>
<code>?_exclude_name__startswith="Test"</code>

----------------------------------------
__istartswith
----------------------------------------
(ignore case) matches values that start with the string parameter<br/>
Example:<br/>
<code>?_exclude_name__istartswith="Test"</code>

----------------------------------------
__contains
----------------------------------------
Matches values that contain the string parameter<br/>
Example:<br/>
<code>?_exclude_name__contains="green"</code>

----------------------------------------
__icontains
----------------------------------------
(ignore case) matches values that contain the string parameter<br/>
Example:<br/>
<code>?_exclude_name__icontains="green"</code>

----------------------------------------
__endswith
----------------------------------------
Matches values that end with the string parameter<br/>
Example:<br/>
<code>?_exclude_name__endswith="s$"</code>

----------------------------------------
__iendswith
----------------------------------------
(ignore case) matches values that end with the string parameter<br/>
Example:<br/>
<code>?_exclude_name__iendswith="s$"</code>

----------------------------------------
__range
----------------------------------------
Matches values within the integer or date parameters<br/>
Example:<br/>
<code>?_filter_create_time__range=("2018-06-19T20:10:41.687799Z","2018-06-19T20:10:41.687799Z")</code><br/>
<code>?_filter_id__range=(755320,755323)</code>

----------------------------------------
__in
----------------------------------------
Matches values that match a value in the list of values in the parameter<br/>
Example:<br/>
<code>?_exclude_label__in=("test","scheduled-weekly")</code><br/>
Any labels that exactly match any of the strings in the list will be excluded from the results

----------------------------------------
__regex
----------------------------------------
Matches string values that match the regex parameter<br/>
Example:<br/>
<code>?_filter_label__regex=".*notable.*"</code>

Fairly complex regex can be handled here but don't be excessive. Most filters or exclusions can be accomplished without regex.

----------------------------------------
__exact and __iexact
----------------------------------------
Exact is essentially useless since a straight = operator gets that job done, but iexact can come in handy occassionally


These can be combined in a url as needed to get the specific results you need<br/>
<code>https://phantomserver.company.com/rest/container?sort=id&order=asc&_filter_playbookrun__container__isnull=True&_filter_ingest_app__isnull=False&_filter_artifact_count__gt=0&_filter_create_time__range=("2019-08-01T00:00:00.000000Z","2019-09-01T00:00:00.000000Z")&_exclude_label__in=("test","scheduled-weekly")</code>



#  Special Notes

----------------------------------------
Black Magic Filtering
----------------------------------------

You can filter on many endpoints with data from others using some undocumented black magic joiny stuff. There is guess work involved and you can't see any of the data from the other referenced endpoints but they can be used to do some cool stuff.

For instance, this rest url is showing data for action_run, but it is being filtered by associated values in playbook_run. This will give you the action_runs where the associated playbook_run had a "failed" status

/rest/action_run?_filter_playbook_run__status="failed"

----------------------------------------

Another example is this

/rest/action_run?_filter_playbook__name__icontains="rule"

This will show only actions runs that were part of a playbook that had "rule" in the playbook name. These can be super helpful and can get you results that you would otherwise need multiple rest calls and some data processing to achieve.

----------------------------------------

One of the most creative and also darkest of magics I have seen with these filters is the this:

/rest/container?_filter_playbookrun__container__isnull=True

This will show containers that have associated playbook_runs with a null container field. This seems like it should show us nothing since a playbook without a container is impossible but it actually shows us the containers that have no associated playbook_runs. 

----------------------------------------

I mentioned that there is guess work involved and hopefully you noticed that in the first example, we filtered with playbook_run and in the second we filtered with playbookrun. These aren't interchangeable.
Most endpoints will spit out a helpful list if you put in bad filter fields so if you are struggling, try running this filter for your endpoint:

?_filter_showmethedata=True

Best of luck on the dark side.
 
----------------------------------------
Playbook Utilities
----------------------------------------

You have to be authenticated with headers, tokens, etc to use these APIs outside of phantom, but inside of custom playbook code and utilities, you have other options.

If you use <br/><code>phantom.requests</code><br/>instead of <br/><code>requests</code><br/>your API request will be automatically passed to the phantom API using the auth of the user executing the playbook (usually automation). This bypasses a lot of potential challenges exposing API tokens and things like that so definitely use the rest API in playbook code but use phantom.requests and make your life a ton easier
