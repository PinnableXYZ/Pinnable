async function doSIWE() {
  let signer = null;
  let provider;
  let address;

  provider = new ethers.BrowserProvider(window.ethereum);

  provider.send('eth_requestAccounts', [])
    .then(async (accounts) => {
      console.log(accounts);
      address = ethers.getAddress(accounts[0]);
    })
    .catch(() => console.log('User rejected account access'));

  signer = await provider.getSigner();

  // message to sign

  const domain = window.location.host;
  const origin = window.location.origin;
  // get the address from provider

  const version = '1';
  const chainId = '1';

  const statement = 'Sign in with Ethereum';

  // Generate a random string contains 17 characters
  const nonce = Math.random().toString(36).substring(2, 11) + Math.random().toString(36).substring(2, 12);

  const issuedAt = new Date().toISOString();

  // Expire in 7 days
  let expirationTime = new Date();
  expirationTime.setDate(expirationTime.getDate() + 7);
  expirationTime = expirationTime.toISOString();

  const messageTemplate = `${domain} wants you to sign in with your Ethereum account:
${address}

${statement}

URI: ${origin}
Version: ${version}
Chain ID: ${chainId}
Nonce: ${nonce}
Issued At: ${issuedAt}
Expiration Time: ${expirationTime}`;

  // sign the message
  const signature = await signer.signMessage(messageTemplate);

  if (signature) {
    const form = document.getElementById('siwe-form');
    const messageInput = form.querySelector(`input[name="message"]`);
    const signatureInput = form.querySelector(`input[name="signature"]`);;
    messageInput.value = messageTemplate;
    signatureInput.value = signature;
    form.submit();
  }

}

function signout() {
  const form = document.getElementById('signout');
  if (form) {
    if (confirm('Are you sure you want to sign out?')) {
      form.submit();
    }
  }
}

function removeWebsite(websiteId) {
  if (confirm('Are you sure you want to remove this website?')) {
    const form = document.getElementById(`remove-website-${websiteId}`);
    form.submit();
  }
}
