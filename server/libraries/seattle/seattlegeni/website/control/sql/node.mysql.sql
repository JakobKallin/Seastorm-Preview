/* We provide sql that django runs after syncdb to perform indexing of the
 * key fields, as the keys are too long to be fully indexed by mysql.
 * Note that if we use db_index=True for these fields in the model, Django
 * 1.1 will create an index on the first field it tries but will not try
 * to index others (and will print an error message). So, we just provide
 * this custom sql.
 * 
 * Note that for InnoDB, the default max key length appears to often be 767 bytes.
 * 
 * When using sqlite3 for development, this custom sql will fail. That's ok.
 * 
 * For more info on providing custom sql after syncdb:
 * http://docs.djangoproject.com/en/dev/howto/initial-data/#providing-initial-sql-data
 */
ALTER TABLE `control_node` ADD INDEX (`node_identifier` (767));
