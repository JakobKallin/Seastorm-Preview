"""
Example of using the seattleclearinghouse_xmlrpc module's SeattleClearinghouseClient.

This script tries to acquire, renew, and release some vessels and prints out
various information along the way.
"""

# This module must be in your python path (for example, in the same directory
# as the current script is in).
import seattleclearinghouse_xmlrpc


USERNAME = "your_username"

# Only one of either the API key or the private key is needed. If providing
# your API key, be sure to pass the API key to the SeattleClearinghouseClient
# constructor below.
#API_KEY = "your_api_key"
PRIVATE_KEY_STRING = open("your_username.privatekey").read()

# Allowing SSL to be insecure means it will be susceptible to MITM attacks.
# See the instructions in seattleclearinghouse_xmlrpc.py for using SSL securely.
ALLOW_SSL_INSECURE = False


def do_example_acquire_renew_release():
  client = seattleclearinghouse_xmlrpc.SeattleClearinghouseClient(username=USERNAME,
                                                private_key_string=PRIVATE_KEY_STRING,
                                                allow_ssl_insecure=ALLOW_SSL_INSECURE)

  # Obtain general information about the account corresponding to the username
  # and API key.
  account_info = client.get_account_info()
  print("Account info: " + str(account_info))

  # Obtain information on vessels already acquired by this account.
  # The value returned is a list of dictionaries where each dictionary
  # describes a vessel.
  already_acquired_vessels = client.get_resource_info()
  print("Vessels already acquired: " + str(already_acquired_vessels))

  print("Number of vessels this account has available to acquire: " +
        str(account_info['max_vessels'] - len(already_acquired_vessels)))

  # Attempt to acquire two vessels on WAN nodes.
  try:
    # This is a list of dictionaries just like the one above.
    newly_acquired_vessels = client.acquire_wan_resources(2)
  except seattleclearinghouse_xmlrpc.NotEnoughCreditsError, err:
    print("Couldn't acquire resources because we don't have enough vessel " +
          "credits: " + str(err))
    return
  except seattleclearinghouse_xmlrpc.UnableToAcquireResourcesError, err:
    print("Couldn't acquire vessels because SeattleGENI doesn't have enough " +
          "of what we asked for: " + str(err))
    return
  print("Acquired WAN vessel: " + str(newly_acquired_vessels))

  acquired_handle_list = []
  for infodict in newly_acquired_vessels:
    acquired_handle_list.append(infodict['handle'])
 
  # Attempt to renew the two vessels we just acquired. 
  try:
    client.renew_resources(acquired_handle_list)
  except seattleclearinghouse_xmlrpc.NotEnoughCreditsError, err:
    # This is probably not going to happen immediately after acquiring vessels.
    print("Couldn't renew vessels because we are over our vessel credit " +
          "limit: " + str(err))
    return
  print("Renewed the vessel we just acquired.")
  
  print("Summary of all of our acquired vessels:")
  all_vessels_list = client.get_resource_info()
  for vesselinfo in all_vessels_list:
    print("Vessel " + str(vesselinfo["vessel_id"]) +
          " on nodemanager accessible at " + str(vesselinfo["node_ip"]) + ":" +
          str(vesselinfo["node_port"]) + " expires in " +
          str(vesselinfo["expires_in_seconds"]) + " seconds.")

  # Release the two vessels we just acquired.
  client.release_resources(acquired_handle_list)
  print("Released the vessel we just acquired.")



def main():
  try:
    do_example_acquire_renew_release()
  except seattleclearinghouse_xmlrpc.SeattleClearinghouseError:
    # In a real script, you'd want to handle this. Could be an authentication
    # error, communication error, etc. You can use the fine-grained exceptions
    # rather than the base exception of SeattleClearinghouseError to do different
    # things based on what the actual problem was.
    raise


if __name__ == "__main__":
  main()
