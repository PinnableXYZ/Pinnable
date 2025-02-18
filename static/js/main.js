async function checkWalletConnection() {
  let siweLabel = document.getElementById("siwe-button-label");
  if (window.ethereum) {
    try {
      // Request list of accounts from user's wallet
      const accounts = await window.ethereum.request({ method: 'eth_accounts' });

      if (accounts.length > 0) {
        // Wallet is connected
        siweLabel.innerHTML = "Sign in with Ethereum";
      } else {
        // Wallet is not connected
        siweLabel.innerHTML = "Connect Wallet";
      }
    } catch (error) {
      console.log(error);
      siweLabel.innerHTML = "Connect Wallet";
    }
  } else {
    // No web3 provider detected
    siweLabel.innerHTML = "Connect Wallet";
  }
}

async function doSIWE() {
  let signer = null;
  let provider;
  let address;

  provider = new ethers.BrowserProvider(window.ethereum);

  provider.send('eth_requestAccounts', [])
    .then(async (accounts) => {
      console.log(accounts);
      address = ethers.getAddress(accounts[0]);
      if (address) {
        let siweLabel = document.getElementById('siwe-button-label');
        siweLabel.innerText = 'Sign in with Ethereum';
      }
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

function formatBytes(value) {
  let val = parseFloat(value);
  if (val > 1024) {
    if (val > 1048576) {
      if (val > 1073741824) {
        return (val / 1073741824.0).toFixed(2) + " GB";
      } else {
        return (val / 1048576.0).toFixed(2) + " MB";
      }
    } else {
      return (val / 1024.0).toFixed(2) + " KB";
    }
  } else {
    return value.toString() + " B";
  }
}

function formatTimestamp(timestamp) {
  const date = new Date(timestamp * 1000);
  const hours = date.getHours();
  const minutes = date.getMinutes();
  const ampm = hours >= 12 ? 'PM' : 'AM';
  const adjustedHours = hours % 12 || 12;
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const month = monthNames[date.getMonth()];
  const day = date.getDate();
  const year = date.getFullYear();
  const timeZone = new Intl.DateTimeFormat('en', { timeZoneName: 'short' }).format(date).split(' ')[1];

  return `${adjustedHours}:${minutes.toString().padStart(2, '0')} ${ampm} · ${month} ${day}, ${year} ${timeZone}`;
}

function removeWebsite(websiteId) {
  if (confirm('Are you sure you want to remove this website?')) {
    const form = document.getElementById(`remove-website-${websiteId}`);
    form.submit();
  }
}

function removeObject(objectId) {
  if (confirm('Are you sure you want to remove this object?')) {
    const form = document.getElementById(`remove-object-${objectId}`);
    form.submit();
  }
}

function toggleVisibility(elem) {
  if (elem.type === "password") {
      elem.type = "text";
  } else {
      elem.type = "password";
  }
}

const copyValue = async (elem) => {
  const copyText = document.getElementById(elem);
  copyText.select();
  copyText.setSelectionRange(0, 99999);
  await navigator.clipboard.writeText(copyText.value);
}

const copyToClipboard = async (text) => {
  await navigator.clipboard.writeText(text);
}
