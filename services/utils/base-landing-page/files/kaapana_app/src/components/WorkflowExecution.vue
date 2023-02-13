
<template lang="pug">
v-dialog(v-model='dialogOpen' max-width='600px')
  template(v-slot:activator='{ on, attrs }')
    v-btn(color="primary" v-bind='attrs' v-on='on' dark) Experiment Execution
  v-card
    v-form(v-model="valid", ref="executeWorkflow", lazy-validation)
      v-card-title
        span.text-h5 Experiment Execution
      v-card-text
        v-container
          v-row
            v-col(cols='12')
              v-text-field(v-model='experiment_name' label='Experiment name' required='')
            v-col(v-if="remote" cols='12')
              v-select(v-model='instance_names' :items='available_instance_names' label='Instance names' multiple='' chips='' hint='On which nodes do you want to execute the workflow')
            v-col(cols='12') 
             
              <v-radio-group v-model="radio_isolation" column>
                <template v-slot:label>
                  <div>Do you want to run your workflow in <strong>Isolation ?</strong></div> 
                  //-v-icon mdi-information
              
                </template>
                <v-radio value="No">
                  <template v-slot:label>
                    <div>No</div>
                  </template>
                </v-radio>
                <v-radio value="Yes">
                  <template v-slot:label>
                    <div>Yes</div>
                  </template>
                </v-radio>
              </v-radio-group>
            v-col(cols='12') 
             <v-radio-group v-model="workflow_type" row>
               <template v-slot:label>
                 <div>Workflow Type:</div> 
                   
               </template>
               <v-radio value="dags">
                 <template v-slot:label>
                   <div>Dags</div>
                 </template>
               </v-radio>
               <v-radio v-if="radio_isolation!=='No'" value="shell_workflow">
                 <template v-slot:label>
                   <div>Bash Script</div>
                 </template>
               </v-radio>
               <v-radio v-if="radio_isolation!=='No'" value="container_workflow">
                 <template v-slot:label>
                   <div>Docker Container</div>
                 </template>
               </v-radio>
             </v-radio-group>
            v-col(v-if="workflow_type =='shell_workflow'" cols='12')
              v-select(v-model='bucket_id' :items='final_available_datasets' label='Choose Dataset' chips='')
            v-col(v-if="workflow_type =='shell_workflow'" cols='12')
              v-text-field(v-model='download_url' label='Enter URL to download shell workflow and supporting scripts (.zip format)' required='')
            //- v-col(v-if="workflow_type =='shell_workflow'" cols='12')
            //-   v-text-field(v-model='bash_cmd' label='Enter your shell workflow command' required='')
            
            v-col(v-if="workflow_type=='container_workflow'" cols='12')
              v-text-field(v-model='docker_registry' label='Enter container registry' required='')
              v-text-field(v-model='docker_uname' label='Enter container registry username' required='')
              v-text-field(v-model='docker_pwd' label='Enter container registry password' required='')
             
            v-col(v-if="instance_names.length && workflow_type!=='shell_workflow' && workflow_type!=='container_workflow' " cols='12')
              v-select(v-model='dag_id' :items='available_dags' label='Dags' chips='' hint='Select a dag')
            
            //- v-if="!(remote==false && name=='federated_form')"
            v-col(v-for="(schema, name) in schemas" cols='12')
              p {{name}}
              v-jsf(v-model="formData[name]" :schema="schema")
          v-row(v-if="external_available_instance_names.length")
            v-col(cols='12')
              h3 Remote Workflow
            v-col(cols='12')
              v-select(v-model='external_instance_names' :items='external_available_instance_names' label='External Instance names' multiple='' chips='' hint='On which (remote) nodes do you want to execute the workflow')
          v-row(v-if="Object.keys(external_schemas).length")
            v-col(v-for="(schema, name) in external_schemas" cols='12')
              p {{name}}
              v-jsf(v-model="formData['external_schema_' + name]" :schema="schema")
          v-row
            v-col(cols='12')
              v-tooltip(v-model='showConfData' top='')
                template(v-slot:activator='{ on, attrs }')
                  v-btn(icon='' v-bind='attrs' v-on='on')
                    v-icon(color='grey lighten-1')
                      | mdi-email
                pre.text-left Experiment name: {{experiment_name}}
                pre.text-left Dag id: {{dag_id}}
                pre.text-left Instance name: {{instance_names}}
                pre.text-left External instance name: {{external_instance_names}}
                pre.text-left Isolation: {{radio_isolation}}
                pre.text-left Workflow Type: {{workflow_type}}
                pre.text-left Bash Url: {{download_url}}
                //- pre.text-left Bash Cmd: {{bash_cmd}}
                pre.text-left Bucket ID: {{bucket_id}}
                pre.text-left Docker Registry: {{docker_registry}}
                pre.text-left Docker Uname: {{docker_uname}}
                pre.text-left Docker Pwd: {{docker_pwd}}

                pre.text-left {{ formDataFormatted }}
      v-card-actions
        v-btn(color="primary", @click="submitWorkflow()"  dark) Start Experiment
        v-btn(color="primary", @click="(instance_names=[]) && (dag_id=null)"  dark) Clear
</template>

<script>
import kaapanaApiService from "@/common/kaapanaApi.service";
import VJsf from "@koumoul/vjsf/lib/VJsf.js";
import "@koumoul/vjsf/lib/VJsf.css";
import "@koumoul/vjsf/lib/deps/third-party.js";
import request from '@/request';

export default {
  name: "WorkflowExecution",
  components: {
    VJsf,
  },
  data: () => ({
    valid: false,
    dialogOpen: false,
    schemas: {},   // changed from {} to [] since we're getting a string and no object
    external_schemas: {}, // changed from {} to [] since we're getting a string and no object
    formData: {},
    // formDataFormatted: {},
    available_dags: [],
    available_minio_buckets: [],
    available_meta_cohorts: [],
    instance_names: [],
    external_instance_names: [],
    external_dag_id: null,
    external_available_instance_names: [],
    experiment_name: null,
    dag_id: null,
    bucket_id: null,
    showConfData: false,
    federated_data: false,
    remote_data:false,
    radio_isolation: 'No',
    workflow_type: 'dags',
    download_url: null,
    // bash_cmd: null,
    docker_registry: null,
    docker_uname: null,
    docker_pwd: null,
  }),
  props: {
    remote: {
      type: Boolean,
      required: true,
    },
    instances: {
      type: Array,
      required: true
    },
    clientinstance: {
      type: Object,
      required: true,
    }
  },
  computed: {
    available_instance_names () {
      console.log("instances: ", this.instances)
      return this.instances.map(({ instance_name }) => instance_name);
    },
    final_available_datasets () {
      //const final_available_datasets  = [...this.available_minio_buckets, ...this.available_meta_cohorts];
      console.log("Final_available_datasets: ", [...this.available_minio_buckets, ...this.available_meta_cohorts])
      return [...this.available_minio_buckets, ...this.available_meta_cohorts]
    },
    formDataFormatted () {
      return this.formatFormData(this.formData)
    }
  },
  mounted() {
  },
  watch: {
    dialogOpen () {
      this.instance_names = []
      this.experiment_name = null
      this.dag_id = null
      this.external_instance_names = []
    },
    instance_names() {
      this.getDags()
      this.getMinioBuckets()
      this.getCohorts()
      this.resetFormData()
    },
    experiment_name() {
      this.resetFormData()
    },
    dag_id() {
      this.resetFormData()
    },
    external_dag_id() {
      this.resetExternalFormData()
    },
    external_instance_names() {
      this.resetExternalFormData()
      if (this.external_instance_names.length) {
        this.getExternalUiFormSchemas()
      }
    }
  },
  methods: {
    formatFormData (formData) {
      // Only necessary because vjsf does not allow to have same keys in selection form with dependencies
      let formDataFormatted = {}
      Object.entries(formData).forEach(([form_key, form_value]) => {
        if (form_key == "workflow_form") {
          formDataFormatted[form_key] = {}
          Object.entries(form_value).forEach(([key, value]) => {
            formDataFormatted[form_key][key.split('#')[0]] = value
          });
        } else {
          formDataFormatted[form_key] = form_value
        }
      });
      return formDataFormatted
    },
    resetFormData() {
      this.schemas = {}
      this.formData = {}
      if (this.remote == false) {
        this.instance_names = this.available_instance_names
      }
      this.resetExternalFormData()
      this.getUiFormSchemas()
      this.external_instance_names = []
    },
    resetExternalFormData() {
      this.external_schemas = {}
      this.external_available_instance_names = []
      // console.log(this.external_dag_id)
      if (this.external_dag_id != null) {
        console.log('getting')
        this.getAvailableExternalNodeIds()
      } else {
      }
      Object.entries(this.formData).forEach(([key, value]) => {
        if (key.startsWith('external_schema_') && (key != ('external_schema_federated_form'))) {
          console.log(`Deleting ${key}: ${value}`)
          delete this.formData[key]
        }
      });

    },
    getUiFormSchemas() {
      // console.log("instance_names:", this.instance_names)
      // this.remote_data = this.remote
      // if (this.instance_names.indexOf(this.clientinstance.instance_name) !== -1) {  // clientinstance is in instance_names ==> local experiment
      //     this.remote_data = false;
      //     console.log("Local Experiment -> remote: ,", this.remote)
      //   }
      kaapanaApiService
        .federatedClientApiPost("/get-ui-form-schemas", {remote: this.remote, experiment_name: this.experiment_name, dag_id: this.dag_id, instance_names: this.instance_names})
        .then((response) => {
          let schemas = response.data
          // console.log("remote: ", this.remote)
          // this.remote = schemas["remote"]
          // console.log("remote: ", this.remote)
          // if (this.remote==false && 'external_schemas' in schemas) {
          if ('external_schemas' in schemas) {
            this.external_dag_id = schemas["external_schemas"]
            delete schemas.external_schemas
          } else {
            this.external_dag_id = null
          }
          // console.log("before schemas: ", schemas)
          this.schemas = schemas
          console.log("after schemas: ", schemas)
        })
        .catch((err) => {
          console.log(err);
        });
    },
    getExternalUiFormSchemas() {
      kaapanaApiService
        .federatedClientApiPost("/get-ui-form-schemas",  {remote: true, experiment_name: this.experiment_name, dag_id: this.external_dag_id, instance_names: this.external_instance_names})
        .then((response) => {
          // console.log("before external_schemas: ", response.data)
          this.external_schemas = response.data
          console.log("after external_schemas: ", this.external_schemas)
        })
        .catch((err) => {
          console.log(err);
        });
    },
    getDags() {
      kaapanaApiService
        .federatedClientApiPost("/get-dags", {remote: this.remote, instance_names: this.instance_names})
        .then((response) => {
          this.available_dags = response.data;
          console.log("Available DAGs: ", this.available_dags)
        })
        .catch((err) => {
          console.log(err);
        });
    },
    getMinioBuckets() {
      kaapanaApiService
        .minioApiget("/buckets")
        .then((response) => {
          this.response = response.data
          const keyName = 'name';
          this.available_minio_buckets = this.response.map(item => item[keyName]);
          //console.log("Available Buckets:", this.available_minio_buckets)
        
        })
        .catch((err) => {
          console.log(err);
        });
    },
    getCohorts() {
      kaapanaApiService
        .federatedClientApiGet("/cohort-names")
        .then((response) => {
          this.available_meta_cohorts = response.data
          //const keyName = 'name';
          //this.available_minio_buckets = this.response.map(item => item[keyName]);
          //console.log("!!!!!!!!!!!!!!!!!!!!!!!!!Available Cohorts:", this.available_meta_cohorts)
        
        })
        .catch((err) => {
          console.log(err);
        });
    },
    getAvailableExternalNodeIds() {
      kaapanaApiService
        .federatedClientApiPost("/get-remote-kaapana-instances", {dag_id: this.external_dag_id})
        .then((response) => {
          this.external_available_instance_names = response.data.map(({ instance_name }) => instance_name);
        })
        .catch((err) => {
          console.log(err);
        });
    },
    submitWorkflow() {

      if (this.radio_isolation !== "No") {
        console.log("TFDA Main Dag Called"
        );
        
        request.post("/flow/kaapana/api/trigger/dag-tfda-testing-workflow", {
            
            'conf': {
            experiment_name: this.experiment_name,
            //dag_id: this.dag_id,
            instance_names: this.instance_names, 
            workflow_type: this.workflow_type,
            download_url: this.download_url,
            // bash_cmd: this.bash_cmd,
            bucket_id: this.bucket_id,
            docker_registry: this.docker_registry,
            docker_uname: this.docker_uname,
            docker_pwd: this.docker_pwd         
            //conf_data: this.formatFormData(this.formData),
            //remote: this.remote_data,
            //federated: this.federated_data,
          },
          })
          .then((response) => {
            this.response = JSON.stringify(response.data);
          })
          .catch((err) => {
            console.log(err);
          });}
      else {
        // modify attributes remote_data and federated_data depending on instances 
        console.log("instance_names: ", this.instance_names)
        // if (this.instance_names.length > 1) {                             // len(instance_names) > 1 ==> federated experiment
        //   this.federated_data = true;
        //   this.remote_data = true;
        //   console.log("Federated Experiment -> federated_data:", this.federated_data, ", remote_data: ,", this.remote_data)
        // }
        // else {                                                            // len(instance_names) = 1 ==> local or remote experiment
        this.federated_data = false;
        console.log("clientinstance.instance_name: ", this.clientinstance.instance_name)
        console.log("client in instances: ", this.instance_names.indexOf(this.clientinstance.instance_name))
        if ((this.instance_names.indexOf(this.clientinstance.instance_name) != -1) && (this.instance_names.length == 1)) {  // clientinstance is in instance_names ==> local experiment
          this.remote_data = false;
          console.log("Local Experiment -> federated_data:", this.federated_data, ", remote_data: ,", this.remote_data)
        }
        else {                                                          // clientinstance is not in instance_names ==> remote experiment
          this.remote_data = true;
          console.log("Remote Experiment -> federated_data:", this.federated_data, ", remote_data: ,", this.remote_data)
        }
        // }
        if (this.external_instance_names.length) {
          this.formData['external_schema_instance_names'] = this.external_instance_names
          this.federated_data = true
        }
        console.log("Experiment executed on: ", this.instance_names)
        kaapanaApiService
          // .federatedClientApiPost("/submit-workflow-schema", {
          .federatedClientApiPost("/experiment", {
            experiment_name: this.experiment_name,
            dag_id: this.dag_id,
            instance_names: this.instance_names,          
            conf_data: this.formatFormData(this.formData),
            remote: this.remote_data,
            federated: this.federated_data,
          })
          .then((response) => {
            this.dialogOpen = false
            console.log(response);
          })
          .catch((err) => {
            console.log(err);
          });
      }
    } }
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
</style>
