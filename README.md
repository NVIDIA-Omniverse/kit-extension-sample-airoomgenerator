# AI Room Generator Extension Sample

![Extension Preview](exts/omni.example.airoomgenerator/data/preview.png)

### About

This extension allows user's to generate 3D content using Generative AI, ChatGPT. Providing an area in the stage and a prompt the user can generate a room configuration designed by ChatGPT. This in turn can help end users automatically generate and place objects within their scene, saving hours of time that would typically be required to create a complex scene.

### [README](exts/omni.example.airoomgenerator)
See the [README for this extension](exts/omni.example.airoomgenerator) to learn more about it including how to use it.

> This sample is for educational purposes. For production please consider best security practices and scalability.

## Adding This Extension

This folder is ready to be pushed to any git repository. Once pushed direct link to a git repository can be added to *Omniverse Kit* extension search paths.

Link might look like this: `git://github.com/NVIDIA-Omniverse/kit-extension-sample-airoomgenerator?branch=main&dir=exts`

Notice `exts` is repo subfolder with extensions. More information can be found in "Git URL as Extension Search Paths" section of developers manual.

To add a link to your *Omniverse Kit* based app go into: Extension Manager -> Gear Icon -> Extension Search Path


## Linking with an Omniverse app

If `app` folder link doesn't exist or broken it can be created again. For better developer experience it is recommended to create a folder link named `app` to the *Omniverse Kit* app installed from *Omniverse Launcher*. Convenience script to use is included.

Run:

```
> link_app.bat
```

If successful you should see `app` folder link in the root of this repo.

If multiple Omniverse apps is installed script will select recommended one. Or you can explicitly pass an app:

```
> link_app.bat --app create
```

You can also just pass a path to create link to:

```
> link_app.bat --path "C:/Users/bob/AppData/Local/ov/pkg/create-2021.3.4"
```


# Contributing
The source code for this repository is provided as-is and we are not accepting outside contributions.
