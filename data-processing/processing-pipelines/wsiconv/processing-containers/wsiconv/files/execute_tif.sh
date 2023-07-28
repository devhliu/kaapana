echo "Hello World"

find $WORKFLOW_DIR/$OPERATOR_IN_DIR -follow -name '*.tif' -exec ./idc-wsi-conversion/gdcsvstodcm_tif.sh '{}' ';'
