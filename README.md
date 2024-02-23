# MAL-Stremio Addon

This Stremio addon allows users to access their anime lists from MyAnimeList (MAL) directly within the Stremio media center. With this addon, you can easily keep track of your watched anime, plan to watch, and more, all from the convenience of Stremio.

## Usage 🧑‍💻

- **User's Anime Lists**: View your personal anime list from MyAnimeList, including the titles you have watched, plan to watch, and any other categories you have set up.
- **Content Tracking and Syncing from within Stremio**:
  - Currently, only Kitsu catalogs are supported.
  - When users watch content in their "plan to watch" list:
    - Shows will be marked as watching and moved to the "watching" list, and the currently watched episode will be updated on MyAnimeList.
    - Movies will be moved to the "completed" list.
  - When users watch content in their "watching" list:
    - Episodes watched will be updated for shows, and a show is marked and moved to the "completed" list when the last episode is watched.
  - When users watch content in their "on hold" list:
    - When a new episode is watched, the show is moved to the "watching" list.

**NOTE**: Due to Stremio not having a native way of handling content tracking, the only way to achieve this is by having Stremio request subtitles from the addon. Instead of returning subtitles, the addon will look at the content that is currently being played that the subtitles are being requested for and mark that content accordingly upon playback, not when the content has been watched all the way through.

## Installation 🛠️

To install the addon:

1. Visit [The Addon Website](https://mal-stremio.vercel.app/) and generate an API Key for MyAnimeList using the "Generate Token" button. This will redirect you to the MyAnimeList authentication page.
2. Log in to your MyAnimeList account and authorize the addon to access your anime list.
3. After authorization, a manifest URL will be generated. Copy the manifest URL.
4. Open Stremio and go to the addon search box.
5. Paste the copied manifest URL into the addon search box and press Enter. Alternatively, you can click "Open In Stremio" to automatically add the addon to Stremio.
6. In Stremio, click install, and the addon will be added and ready for use.

**NB**: If no content is being displayed, it could be the result of your session expiring. To renew your session, return to the [Addon's website](https://mal-stremio.vercel.app/) to "Sign in with MyAnimeList" or "Refresh MyAnimeList Session". Afterwards, content should then show up in Stremio.

## Support

If you encounter any issues or have any questions regarding the addon, feel free to [report them here](https://github.com/SageTendo/mal-stremio-addon/issues).

## API References

This addon is developed using the following API references:

- **Stremio Addon SDK**: This SDK provides the necessary tools and functions to create addons for Stremio. You can refer to the [official Stremio Addon SDK documentation](https://github.com/Stremio/stremio-addon-sdk) for more information.

- **MyAnimeList (MAL)**: MyAnimeList is a popular online community and database for anime and manga enthusiasts. This addon utilizes the MyAnimeList API to fetch and display user-specific anime list data. You can explore the [MyAnimeList API Documentation](https://myanimelist.net/apiconfig/references/api/v2) for more details.

- **Stremio-Kitsu-Anime**: Unofficial Kitsu anime catalog for Stremio. Credits to [TheBeastLT](https://github.com/TheBeastLT/stremio-kitsu-anime).

Please refer to these API references for detailed information on how to interact with the respective APIs.

## Acknowledgements

- **Animeo**: Inspiration for the content syncing functionality. [More info here](https://github.com/Jenrykster/animeo).
