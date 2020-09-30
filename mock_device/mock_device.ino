enum Result {
  OK,
  ERR,
  EXIT
};

void setup() {
  Serial.begin(115200);
}

void loop() {
  startup();
  delay(500);
  authenticate();
  run_commands();
}

void authenticate() {
  while (true) {
    Serial.println("Enter secret password");
    String password = read_line();
    if (password == "hunter2") {
      Serial.println("Logged in");
      return;
    } else {
      Serial.println("Wrong password");
    }
  } 
}

void startup() {
  Serial.println("Booting...");
  delay(3000);
  Serial.println("Loading blocks...");
  for (int i = 0; i < 10; i++) {
    delay(200);
    Serial.print("Block ");
    Serial.print(i);
    Serial.println(" loaded");
  }
  Serial.println("Starting user space");
}

bool run_commands() {
  while (true) {
    Serial.println("Enter command");
    String command = read_line();
    Result result = run_command(command);
    if (result == OK) {
      Serial.println("OK");
    } else if (result == ERR) {
      Serial.println("ERROR");
    } else {
      Serial.println("OK");
      Serial.println("Powering off...");
      delay(3000);
      return;
    }
  }
}

Result run_command(String command) {
  if (command == "ping") {
    Serial.println("pong");
    return OK;
  } else if (command == "version") {
    Serial.println("v1.0");
    return OK;
  } else if (command == "reset") {
    Serial.println("Resetting...");
    delay(500);
    Serial.println("Reset complete");
    return EXIT;
  } else if (command == "calculate") {
    Serial.println("42");
    return OK;
  } else {
    Serial.println("Unknown command");
    return ERR;
  }
}

String read_line() {
  String line = "";
  while (line == "") {
    line = Serial.readStringUntil("\n");
  }
  line.trim();
  Serial.println(line);
  return line;
}

