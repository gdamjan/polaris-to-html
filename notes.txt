The `polaris_sf_cd-rom_[complete].zip` has both lower case and upper case filenames, but all the links in the html documents use lower case. Thus the archive was unziped with `unzip -LL polaris_sf_cd-rom_[complete].zip -d polaris_sf_complete`.

Additionally, the `menu.html` has backward slashes, so to fix that use: `sed -i 's|\.\.\\|../|' polaris_sf_complete/html/menu.html`.