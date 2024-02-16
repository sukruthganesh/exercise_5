/* For room.html */

// TODO: Fetch the list of existing chat messages.
// POST to the API when the user posts a new message.
// Automatically poll for new messages on a regular interval.
// Allow changing the name of a room
const api_key = WATCH_PARTY_API_KEY;  
const user_id = WATCH_PARTY_USER_ID;
const ALL_MESSAGES = '/api/room/messages';
const POST_MESSAGE = '/api/room/new_msg';
const CHANGE_USERNAME = '/api/user/name';
const CHANGE_PASSWORD = '/api/user/password';
const CHANGE_ROOM = '/api/room/name';
let max_id = 0;

let getAllChatsReq = {
  room_id: 0
};

let postRequest = {
  room_id: 0,
  body: ''
};

let updateUserNameRequest = {
  user_name: ''
};

let updatePasswordRequest = {
  password: ''
};

let updateRoomRequest = {
  name: '',
  room_id: 0
};

async function generateUrl(endPoint, requestBody, type){
  let url = endPoint + "?" + Object.keys(requestBody).map((key) => key+"="+encodeURIComponent(requestBody[key])).join("&");
  let urlHeaders = new Headers();
  urlHeaders.append("Api-Key", api_key);
  urlHeaders.append("Accept", "application/json");
  urlHeaders.append("Content-Type", "application/json");
  urlHeaders.append("User-Id", user_id);

  if(endPoint == CHANGE_PASSWORD){
    urlHeaders.append("Password", Object.keys(requestBody).map((key) => requestBody[key]).join(''));
    url = endPoint;
  }

  const dict = {
    method: type,
    headers: urlHeaders,
  };

  data = await fetch(url, dict);
  jsonForm = await data.json();
  return jsonForm
}

async function handleChangeUserName() {
  updateUserNameRequest.user_name = document.getElementById('usrName').value;
  postMsg = await generateUrl(CHANGE_USERNAME, updateUserNameRequest, 'POST');
  return;
} 

async function handleUpdatePassword() {
  updatePasswordRequest.password = document.getElementById('pass').value;
  postMsg = await generateUrl(CHANGE_PASSWORD, updatePasswordRequest, 'POST');
  return;
}

async function postMessage(room_id) {
  postRequest.room_id = room_id;
  postRequest.body = document.querySelector('.comment_box textarea').value;
  postMsg = await generateUrl(POST_MESSAGE, postRequest, 'POST');
  document.querySelector(".comment_box form").reset();
  return;
}

async function getMessages(room_id) {
  getAllChatsReq.room_id = room_id;
  let msgs = await generateUrl(ALL_MESSAGES, getAllChatsReq, 'GET')
  let msgsDiv = document.body.querySelector(".messages");
  let child = msgsDiv.lastElementChild;
  while (child) {
    msgsDiv.removeChild(child);
    child = msgsDiv.lastElementChild;
  }

  Object.keys(msgs).forEach(key => {
    let msg = document.createElement("message");
    let author = document.createElement("author");
    author.innerHTML = msgs[key].name;
    let content = document.createElement("content");
    content.innerHTML = msgs[key].body;
    msg.appendChild(author);
    msg.appendChild(content);
    msgsDiv.append(msg);
  });
  return;
}

async function startMessagePolling(room_id) {
  setInterval(async () => {
    await getMessages(room_id);
  }, 100);
  return;
}

async function updateRoomName(room_id) {
  newRoomName = document.querySelector('.edit input').value;
  updateRoomRequest.name = newRoomName;
  updateRoomRequest.room_id = room_id;
  let resp = await generateUrl(CHANGE_ROOM, updateRoomRequest, 'POST');
  edit_h3 = document.querySelector(".display");
  edit_h3.classList.remove("hide");
  edit_input = document.querySelector(".edit");
  edit_input.classList.add("hide");
  document.querySelector('.display .roomName').innerHTML = updateRoomRequest.name;
}

function handleClickEditRoom() {
  edit_input = document.querySelector(".edit");
  edit_input.classList.remove("hide");
  edit_h3 = document.querySelector(".display");
  edit_h3.classList.add("hide");
}

/* For profile.html */

// TODO: Allow updating the username and password
