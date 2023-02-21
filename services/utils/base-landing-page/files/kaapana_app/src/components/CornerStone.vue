<template>
  <div class="parent">
    <div ref="canvas" class="cover" oncontextmenu="return false"/>
    <div v-if="loading" class="cover overlay">
      <v-row
          class="fill-height ma-0"
          align="center"
          justify="center"
      >
        <v-progress-circular
            indeterminate
            color="primary"
        />
      </v-row>
    </div>
  </div>
</template>

<script>
/* eslint-disable */

// Packages
import {
  RenderingEngine,
  Types,
  Enums,
  setVolumesForViewports,
  volumeLoader,
  imageLoader
} from '@cornerstonejs/core';
import * as cornerstone from "@cornerstonejs/core";
import * as cornerstoneTools from '@cornerstonejs/tools';
import createImageIdsAndCacheMetaData from "../utils/cornerstone/createImageIdsAndCacheMetaData";
import {addTool, StackScrollMouseWheelTool, ToolGroupManager, WindowLevelTool, ZoomTool} from "@cornerstonejs/tools";
import {MouseBindings} from "@cornerstonejs/tools/dist/cjs/enums";
import initDemo from "../utils/cornerstone/initDemo";

const {
  SegmentationDisplayTool,
  Enums: csToolsEnums,
  segmentation,
} = cornerstoneTools;

const {ViewportType} = Enums;

const volumeName = 'CT_VOLUME_ID'; // Id of the volume less loader prefix
const volumeLoaderScheme = 'cornerstoneStreamingImageVolume'; // Loader id which defines which volume loader to use
// const volumeId = `${volumeLoaderScheme}:${volumeName}`; // VolumeId with loader id + volume id
const segmentationId = 'MY_SEGMENTATION_ID';
const toolGroupId = 'ToolGroup';
const renderingEngineId = 'renderEngine'
const viewportId = 'Cornerstone'

function createMockEllipsoidSegmentation(segmentationVolume) {
  const scalarData = segmentationVolume.scalarData;
  const {dimensions} = segmentationVolume;

  const center = [dimensions[0] / 2, dimensions[1] / 2, dimensions[2] / 2];
  const outerRadius = 50;
  const innerRadius = 10;

  let voxelIndex = 0;

  for (let z = 0; z < dimensions[2]; z++) {
    for (let y = 0; y < dimensions[1]; y++) {
      for (let x = 0; x < dimensions[0]; x++) {
        const distanceFromCenter = Math.sqrt(
            (x - center[0]) * (x - center[0]) +
            (y - center[1]) * (y - center[1]) +
            (z - center[2]) * (z - center[2])
        );
        if (distanceFromCenter < innerRadius) {
          scalarData[voxelIndex] = 1;
        } else if (distanceFromCenter < outerRadius) {
          scalarData[voxelIndex] = 2;
        }

        voxelIndex++;
      }
    }
  }
}

async function addSegmentationsToState(volumeId) {
  // Create a segmentation of the same resolution as the source data
  // using volumeLoader.createAndCacheDerivedVolume.
  const segmentationVolume = await volumeLoader.createAndCacheDerivedVolume(
      volumeId,
      {
        volumeId: segmentationId,
      }
  );

  // Add the segmentations to state
  segmentation.addSegmentations([
    {
      segmentationId,
      representation: {
        // The type of segmentation
        type: csToolsEnums.SegmentationRepresentations.Labelmap,
        // The actual segmentation data, in the case of labelmap this is a
        // reference to the source volume of the segmentation.
        data: {
          volumeId: segmentationId,
        },
      },
    },
  ]);

  // Add some data to the segmentations
  createMockEllipsoidSegmentation(segmentationVolume);
}

initDemo()

// TODO: Segmentation support
// TODO: Decision rule whether to go with Stack viewer or volume viewer
// TODO: Cancel loading once new file is selected

export default {
  name: "CornerStone",
  props: {
    seriesInstanceUID: {
      type: String,
    },
    studyInstanceUID: {
      type: String,
    },
  },
  data() {
    return {
      loading: false,
      renderingEngine: null,
    }
  },
  methods: {
    async load_volume(imageIds) {
      this.renderingEngine.enableElement({
        viewportId: viewportId,
        type: ViewportType.ORTHOGRAPHIC,
        element: this.$refs.canvas,
        defaultOptions: {
          orientation: Enums.OrientationAxis.AXIAL,
        },
      });

      const volumeId = this.seriesInstanceUID

      // Define a volume in memory
      const volume = await volumeLoader.createAndCacheVolume(volumeId, {
        imageIds,
      });

      // Add some segmentations based on the source data volume
      // await addSegmentationsToState();

      volume.load();

      // Set volumes on the viewports
      await setVolumesForViewports(
          this.renderingEngine,
          [{volumeId}],
          [viewportId]
      );

      // // Add the segmentation representation to the toolgroup
      // await segmentation.addSegmentationRepresentations(toolGroupId, [
      //   {
      //     segmentationId,
      //     type: csToolsEnums.SegmentationRepresentations.Labelmap,
      //   },
      // ]);
      // Render the image
      this.renderingEngine.renderViewports([viewportId]);

    },

    async load_stack(imageIds) {
      this.renderingEngine.setViewports([
        {
          viewportId: viewportId,
          type: ViewportType.STACK,
          element: this.$refs.canvas,
          defaultOptions: {
            orientation: Enums.OrientationAxis.AXIAL,
          },
        },
      ]);

      imageLoader.loadAndCacheImages(imageIds)
      const viewport = this.renderingEngine.getViewport(viewportId);
      await viewport.setStack(imageIds);

      viewport.render()
    },

    async load_data() {
      // Get Cornerstone imageIds for the source data and fetch metadata into RAM
      const imageIds = await createImageIdsAndCacheMetaData({
        StudyInstanceUID: this.studyInstanceUID,
        SeriesInstanceUID: this.seriesInstanceUID,
        wadoRsRoot: process.env.VUE_APP_RS_ENDPOINT,
      });
      if (this.renderingEngine !== null) {
        this.renderingEngine.destroy()
      }

      this.renderingEngine = new RenderingEngine(renderingEngineId);

      addTool(ZoomTool);
      addTool(StackScrollMouseWheelTool);
      addTool(WindowLevelTool);
      addTool(SegmentationDisplayTool);

      const toolGroup = ToolGroupManager.createToolGroup(toolGroupId);

      // Add tools to the ToolGroup
      toolGroup.addTool(ZoomTool.toolName);
      toolGroup.addTool(StackScrollMouseWheelTool.toolName);
      toolGroup.addTool(WindowLevelTool.toolName);
      // toolGroup.addTool(SegmentationDisplayTool.toolName);

      toolGroup.addViewport(viewportId, renderingEngineId);

      toolGroup.setToolActive(StackScrollMouseWheelTool.toolName);

      toolGroup.setToolActive(WindowLevelTool.toolName, {
        bindings: [
          {
            mouseButton: MouseBindings.Primary, // Left Click
          },
        ],
      });

      toolGroup.setToolActive(ZoomTool.toolName, {
        bindings: [
          {
            mouseButton: MouseBindings.Secondary, // Right Click
          },
        ],
      });
      // toolGroup.setToolEnabled(SegmentationDisplayTool.toolName);

      try {
        console.log('rendering volume')
        await this.load_volume(imageIds)
      } catch (e) {
        console.log(e)
        await this.load_stack(imageIds)
        console.log('rendering stack')
      }
    }
  },
  updated() {
  },
  created() {
  },
  async mounted() {
    this.renderingEngine = new RenderingEngine(renderingEngineId);

    addTool(ZoomTool);
    addTool(StackScrollMouseWheelTool);
    addTool(WindowLevelTool);
    addTool(SegmentationDisplayTool);

    const toolGroup = ToolGroupManager.createToolGroup(toolGroupId);

    // Add tools to the ToolGroup
    toolGroup.addTool(ZoomTool.toolName);
    toolGroup.addTool(StackScrollMouseWheelTool.toolName);
    toolGroup.addTool(WindowLevelTool.toolName);
    // toolGroup.addTool(SegmentationDisplayTool.toolName);

    toolGroup.addViewport(viewportId, renderingEngineId);

    toolGroup.setToolActive(StackScrollMouseWheelTool.toolName);

    toolGroup.setToolActive(WindowLevelTool.toolName, {
      bindings: [
        {
          mouseButton: MouseBindings.Primary, // Left Click
        },
      ],
    });

    toolGroup.setToolActive(ZoomTool.toolName, {
      bindings: [
        {
          mouseButton: MouseBindings.Secondary, // Right Click
        },
      ],
    });
    // toolGroup.setToolEnabled(SegmentationDisplayTool.toolName);

    this.load_data();
  },
  watch: {
    seriesInstanceUID() {
      this.load_data();
    },
    loading() {
      console.log(`loading: ${this.loading}`)
    },
  },
};
</script>

<style>
.parent {
  position: relative;
  height: 300px;
  width: 100%;
}

.cover {
  position: absolute;
  height: 100%;
  width: 100%;
  display: block;
}

.overlay {
  background: rgba(255, 255, 255, .5);
}
</style>
