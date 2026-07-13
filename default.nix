{
  buildPythonApplication,
  lib,
  textual,
  pytestCheckHook,
  paho-mqtt,
  httpx,
  pyyaml,
  setuptools,
}:

buildPythonApplication {
  pname = "emfdash";
  version = (builtins.fromTOML (builtins.readFile ./pyproject.toml)).project.version;
  pyproject = true;

  src = ./.;

  nativeBuildInputs = [ pytestCheckHook ];

  propagatedBuildInputs = [
    setuptools
    textual
    paho-mqtt
    httpx
    pyyaml
  ];

  meta = {
    description = "An ncurses-style TUI dashboard for EMF Camp. Currently supporting schedule, personal favourites, films, weather, phones and arbitrary MQTT feed data.";
    mainProgram = "emfdash";
    homepage = "https://github.com/cablespaghetti/emfdash";
    platforms = lib.platforms.unix;
  };
}
