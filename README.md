# SROTD Schedule Bot

The Open Source version of the bot that runs and maintains the system behind the over 1.1 million users following SubredditOfTheDay and TinySubredditOfTheDay

## Features

* Automatic Schedule Creation
  * Also updating a reddit spreadsheet with new entries
* Handling of Flairs
* Safety Checks
* Discord Integration
  * Webhook based updates to drafts, posts and more
  * Embed creation
* Extensive logging

## Usage

1. ```virtualenv env```
2. ```source env/bin/activate```
3. ```python -m pip -r requirements.txt```
4. Add all needed informations into "config.py" (See PRAW Docs)
5. ```python main.py```

*It is recommended to run the bot through a timed systemd service every 15-or-so minutes*

## License

This work is under the [European Union Public License v1.2](LICENSE) or – as soon they will be approved by the European Commission - subsequent versions of the EUPL (the "Licence");

You may get a copy of this license in your language from the European Commission [here](https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12).

Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

See the Licence for the specific language governing permissions and limitations under the Licence.