#!/bin/bash

# Generate the Slides and Pages
FILES=$(find . -type f -name '*.ipynb')

for f in $FILES; do
   if [[ $f =~ "ipynb_checkpoints" ]]; then
      echo "Removing ipynb_checkpoints folder"
      rm -rf $f 
      continue
   fi
   filename=$(basename "$f")
   extension="${filename##*.}"
   filename="${filename%.*}"

   if [[ $extension == "ipynb" ]]; then
      echo "Jupyter - $filename"
      if [ ! -e  docs/"$filename".html ]; then 
         jupyter nbconvert  $f --output ../docs/"$filename".html
      fi


   fi

   # Convert the Notebook to Markdown
   #jupyter-nbconvert --to markdown Notebooks/"$filename".ipynb
   # Move to the Markdown directory
   #mv Notebooks/"$filename".md  Markdown/"$filename".md

done

FILES=$(find . -type f -name '*.md' ! -path "./docs*" ! -name "README.md" ! -name "index.md")

for f in $FILES; do
   filename=$(basename "$f")
   extension="${filename##*.}"
   filename="${filename%.*}"
   directory=$(dirname "$f")

   if [[ $extension == "md" ]]; then
      echo "RStudio - $directory"
      rsync -r $directory/* docs
   fi

	

   # Convert the Notebook to Markdown
   #jupyter-nbconvert --to markdown Notebooks/"$filename".ipynb
   # Move to the Markdown directory
   #mv Notebooks/"$filename".md  Markdown/"$filename".md

done

find ./docs -type d -empty -delete

# Push the updates to gh-pages
git add docs/.
git commit -m "Updating Docs"
git push 
