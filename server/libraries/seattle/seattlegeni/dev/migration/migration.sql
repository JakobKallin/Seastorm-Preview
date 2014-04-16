/*
 * <Author>
 *   Justin Samuel
 *
 * <Date started>
 *   14 August 2009
 *
 * <Purpose>
 *   This is a sql script to migrate data from the old seattlegeni database
 *   to the new one. It assumes the old database is named `geni` and the new
 *   one is named `seattlegeni`.
 *
 *   There is some invalid data in the old database, so that also finds its
 *   way into the new database after migration. However, there's should be
 *   less incorrect state (and it should be more obvious when something is
 *   incorrect). For details, read through the rest of the comments in this
 *   file.
 */

/*
The following tables are not migrated because it either a) doesn't make
sense to do so, b) the data does not appear to be current or, c) the tables
are empty:

auth_group
auth_group_permissions
auth_message
auth_permission
auth_user_groups
auth_user_user_permissions
django_admin_log
django_content_type
django_session django_site
 */



/* Disable checking of foreign key constraints. */
SET foreign_key_checks = 0;



/* Empty all of the tables we're going to populate. They should already be
   empty, though. */
TRUNCATE seattlegeni.auth_user ;
TRUNCATE seattlegeni.auth_user_groups ;
TRUNCATE seattlegeni.auth_user_user_permissions ;
TRUNCATE seattlegeni.control_donation ;
TRUNCATE seattlegeni.control_geniuser ;
TRUNCATE seattlegeni.control_node ;
TRUNCATE seattlegeni.control_vessel ;
TRUNCATE seattlegeni.control_vesselport ;
TRUNCATE seattlegeni.control_vesseluseraccessmap ;
TRUNCATE keydb.keys ;





/*
Order of fields in the new control_node table:

id
node_identifier
last_known_ip
last_known_port
last_known_version
date_last_contacted
is_active
is_broken
owner_pubkey
extra_vessel_name
date_created
date_modified

WARNING:
There appear to be two active nodes without extra vessels. You can find them
after the migration using the following:
  SELECT * FROM seattlegeni.control_node WHERE extra_vessel_name = '' AND is_active = 1 
They appear to be nodes id 3413 and 3475 and they actuall appear to not have any vessels.
You can check this on the old database with:
  SELECT * FROM geni.control_vessel WHERE donation_id IN (3413, 3475)

WARNING: 
Some vessel records in the old database indicate there is more than one extra vessel on a node:
   SELECT donation_id FROM geni.control_vessel GROUP BY donation_id HAVING SUM(extra_vessel) > 1
The ids 1295, 2476, 2486, 3500 were obtained from the query above.
Note that node 3500 looks like it may be an active node, so this one might require manual work
after the migration to get the database in the right state for it.
This is the reason we have the LIMIT 1 in the subquery to get the extra vessel's name below.

Note:
After the import, we can compare the list of extra vessels between the old and new
databases by comparing the output of the following two queries:
  1) SELECT donation_id, name FROM geni.control_vessel WHERE extra_vessel = 1 ORDER BY donation_id
  2) SELECT id, extra_vessel_name FROM seattlegeni.control_node WHERE extra_vessel_name <> '' ORDER BY id
The result should match with the exception of the nodes (1295, 2476, 2486, 3500) that have multiple
vessel records in the old db that are marked as extra vessels.
Here's the difference with a diff of the two outputs:
$ diff old.out new.out
1c1
< donation_id   name
---
> id    extra_vessel_name
937d936
< 1295  v33
1680d1678
< 2476  v33
1690,1692d1687
< 2486  v45
< 2486  v83
< 2486  v103
2608d2602
< 3500  v33
*/
INSERT INTO seattlegeni.control_node
  SELECT 
    old_donation.id,
    old_donation.pubkey,
    old_donation.ip,
    old_donation.port,
    old_donation.version,
    /* The old seattlegeni didn't keep a meaningful last_heard value, but we don't want
     * django to consider this NULL, which it seems to if it's 0000-00-00 00:00:00. */
    NOW(),
    old_donation.active,
    FALSE,
    old_donation.owner_pubkey,
    /* We'll get an empty string in the database when there isn't an extra_vessel for this node. */
    (SELECT name FROM geni.control_vessel WHERE donation_id = old_donation.id AND extra_vessel = 1 LIMIT 1),
    NOW(),
    NOW()
  FROM geni.control_donation AS old_donation;





/*
Order of fields in the new control_donation table:

id
node_id
donor_id
status
resource_description_text
date_created
date_modified
*/
INSERT INTO seattlegeni.control_donation
  SELECT 
    old_donation.id, /* The same as the node id because of a 1-to-1 mapping at the moment. */
    old_donation.id, /* Also the same as the node id (because this is the node_id field). */
    /* The user id from the django auth_user table, not the control_user table. */
    (SELECT www_user_id FROM geni.control_user WHERE id = old_donation.user_id),
    '', /* We're not sure we're actually going to keep the donation status field and there's nothing that corresponds to it. */
    '', /* We don't have the resource_description_text data for existing donations. */
    NOW(),
    NOW()
  FROM geni.control_donation AS old_donation;





/*
Order of fields in the new control_vessel table:

id
node_id
name
acquired_by_user_id
date_acquired
date_expires
is_dirty
date_created
date_modified

Note that we use the old control_vesselport table (singular) rather than the
old control_vesselports table (plural). The table with the singular name is
the one in current use and acquired vessels will refer to ids in that table.
*/
INSERT INTO seattlegeni.control_vessel
  SELECT 
    old_vessel.id,
    old_vessel.donation_id,
    old_vessel.name,

    /* Note: the "assigned" field in the old control_vessel table appears to be unused and
       so not an indicator of whether the vessel has been acquired. */

   /* User who acquired the vessel is linked through the old control_vesselport table. */
   (SELECT control_user.www_user_id
    FROM geni.control_vesselmap vmap,
         geni.control_vesselport vport,
         geni.control_user
    WHERE vmap.vessel_port_id = vport.id AND
          vport.vessel_id = old_vessel.id AND
          control_user.id = vmap.user_id),

    NULL, /* The old database didn't track the date acquired. */

   /* Vessel expiration date is linked through the old control_vesselport table. */
   (SELECT vmap.expiration
    FROM geni.control_vesselmap vmap,
         geni.control_vesselport vport
    WHERE vmap.vessel_port_id = vport.id AND
          vport.vessel_id = old_vessel.id),

    0, /* We don't consider the vessel dirty initially as that was not represented in the old database. */
    NOW(),
    NOW()
  FROM geni.control_vessel AS old_vessel
  WHERE old_vessel.extra_vessel = 0;




/*
 The ports in the old database are split across two tables of the same format
 with a clean split in vessel_id values (one table is 1-4009, the other 4009+).
 So, I'm assuming that the name of the model class was changed and the new table
 created off that name, but the existing vesselport records weren't moved over
 to the new table. We'll import both tables into the new database, starting with
 the table with the plural name (control_vesselports).
*/
INSERT INTO seattlegeni.control_vesselport
  SELECT NULL, vessel_id, port FROM geni.control_vesselports;

INSERT INTO seattlegeni.control_vesselport
  SELECT NULL, vessel_id, port FROM geni.control_vesselport;




/*
Order of fields in the new control_vesseluseraccessmap table:

id
vessel_id
user_id
date_created

For now, there's only a mapping between acquired vessels and the user who acquired them
     as the set of control_vesseluseraccessmap entries.
*/
INSERT INTO seattlegeni.control_vesseluseraccessmap
  SELECT NULL, /* Tell mysql to autoincrement the id field */
         id,
         acquired_by_user_id,
         NOW()
  FROM seattlegeni.control_vessel
  WHERE acquired_by_user_id IS NOT NULL;





INSERT INTO seattlegeni.auth_user
  SELECT * FROM geni.auth_user;




/*
Order of fields in the new control_geniuser table:

user_ptr_id
usable_vessel_port
affiliation
user_pubkey
user_privkey
api_key
donor_pubkey
free_vessel_credits
date_created
date_modified
*/
INSERT INTO seattlegeni.control_geniuser
  SELECT old_geniuser.www_user_id,
         old_geniuser.port,
         old_geniuser.affiliation,
         old_geniuser.pubkey,
         IF(old_geniuser.privkey <> "", old_geniuser.privkey, NULL),
         '',
         old_geniuser.donor_pubkey,
         old_geniuser.vcount_base,
         NOW(),
         NOW()
  FROM geni.control_user AS old_geniuser;




/*
Now we insert the private keys into the keydb.

There are two different types of private keys we store in the keydb:
  * Donor privkeys
  * Node owner privkeys
*/

/* First, there's a node owner key that is the duplicate of another. Both appear
   to be inactive nodes. We'll just prepend to one of the pubkeys a note
   that it's a duplicate, thereby at least making it importable into the
   new key database by not being a duplicate any longer. */
UPDATE geni.control_donation 
SET owner_pubkey  = CONCAT("Duplicate key with node 2460 found during migration! ", owner_pubkey)
WHERE id = 2583;

/*
Order of fields in the new keydb.keys table:

id
pubkeyhash
pubkey
privkey
description
*/
/* Insert the donor private keys into the keydb. */
INSERT INTO keydb.keys
  SELECT NULL, /* Tell mysql to autoincrement the id field */
         MD5(old_geniuser.donor_pubkey),
         old_geniuser.donor_pubkey,
         old_geniuser.donor_privkey,
         CONCAT("donor:", old_authuser.username)
  FROM geni.control_user AS old_geniuser,
       geni.auth_user AS old_authuser
  WHERE old_authuser.id = old_geniuser.www_user_id;

/* Insert the node owner private keys into the keydb. */
INSERT INTO keydb.keys
  SELECT NULL, /* Tell mysql to autoincrement the id field */
         MD5(owner_pubkey),
         owner_pubkey,
         owner_privkey,
         CONCAT("node:", id)
  FROM geni.control_donation


