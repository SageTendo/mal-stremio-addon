# MAL-Stremio Addon

This Stremio addon enables users to access their anime list from MyAnimeList (MAL) directly within the Stremio media
center.
With this addon, you can easily keep track of your watched anime, plan to watch, and more, all from the convenience of
Stremio.

<b><font color="#FFFF00">
NB: Currently, this addon only handles catalogs. To get details and streams on a catalog item (anime), Anime Kitsu
and Torrentio addons addon must be installed alongside this addon.
</b></font>

## Installation

To install the MyAnimeList Anime List addon, please follow these steps:

1. Visit [The Addon Website](https://mal-stremio.vercel.app/) and generate an API Key for MyAnimeList using the "
   Generate Token" button. This will redirect you to the MyAnimeList authentication page.
2. Login to your MyAnimeList account and authorize the addon to access your anime list.
3. After authorization, a manifest URL will be generated. Copy the manifest URL.
4. Open the Stremio media center and go to the addon search box.
5. Paste the copied manifest URL into the addon search box and press Enter. Alternatively, you can click the magnet URL
   generated on the website to automatically add the addon to Stremio.
6. The MyAnimeList Anime List addon will be added to your Stremio and ready for use.

## Usage

Once you have installed the MyAnimeList Anime List addon, you can access it within the Stremio media center. The addon
provides the following features:

- **Anime List**: View your personal anime list from MyAnimeList, including the titles you have watched, plan to watch,
  and any other categories you have set up.

## Support

If you encounter any issues or have any questions regarding the addon, feel free
to [report them here](https://github.com/SageTendo/mal-stremio-addon/issues).

## API References

This addon is developed using the following API references:

- **Stremio Addon SDK**: This SDK provides the necessary tools and functions to create addons for Stremio. You can refer
  to the [official Stremio Addon SDK documentation](https://github.com/Stremio/stremio-addon-sdk) for more information.

- **MyAnimeList (MAL)**: MyAnimeList is a popular online community and database for anime and manga enthusiasts. This
  addon utilizes the MyAnimeList API to fetch and display user-specific anime list data. You can explore
  the [MyAnimeList API Documentation](https://myanimelist.net/apiconfig/references/api/v2) for more details.

- **Stremio-Kitsu-Anime**: Unofficial Kitsu anime catalog for Stremio. Credits
  to [TheBeastLT](https://github.com/TheBeastLT/stremio-kitsu-anime).

Please refer to these API references for detailed information on how to interact with the respective APIs.
