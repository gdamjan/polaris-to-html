The `polaris_sf_cd-rom_[complete].zip` has both lower case and upper case filenames, but all the links in the html documents use lower case. Thus the archive was unziped with `unzip -LL polaris_sf_cd-rom_[complete].zip -d polaris_sf_complete`.

Additionally, the `menu.html` has backward slashes, so to fix that use: `sed -i 's|\.\.\\|../|' polaris_sf_complete/html/menu.html`.

Them, after the script below creates a single .html page for each  book, you can run:

    ebook-convert single-page-book.html single-page-book.azw3 \
        --level1-toc '//h:h2' --level2-toc '//h:h3' \
        --page-breaks-before "//*[name()='h1' or name()='h2' or name()='h3']" \
        --cover cover.jpg

To run it on the whole collection:

     find polaris_sf_complete/html/* -type d -print0 |
     xargs -0 --verbose -P3 -I{}  sh -c "cd {}; polaris-to-ebook.py --epub" &> out.log

kind of ugly with the `sh -c "cd {}; ...` but I'm lazy to implement chdir in the program itself.
