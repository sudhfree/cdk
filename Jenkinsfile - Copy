pipeline {
    
    agent {
        dockerfile {
		args "-v /etc/passwd:/etc/passwd -u root:root"
		}
    }

    stages {
        stage('Hello') {
            steps {
                script{
                //sh 'docker built -t test .'
                //def image = docker.build('test:1.0')
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', accessKeyVariable: 'AWS_ACCESS_KEY_ID', credentialsId: 'awsid', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY']]) {
    // some block
deployfile = "deploy_"+"$environment"+".sh"
                sh "export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && cd deployment && python -m pip install -r requirements.cdk.txt &&  ./$deployfile"
                }

                            }
        }
    }
}

}